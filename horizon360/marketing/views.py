import json
from decimal import Decimal
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView

from cdp_core.models import RawEvent, Customer, Segment
from .models import (
    Campaign, CampaignSegment, CampaignContent, CampaignRecipient,
    CampaignEvent, CampaignPropensityScore, AttributionTouchpoint,
    Lead, CampaignTransaction
)
from .serializers import (
    CampaignSerializer, CampaignContentSerializer, CampaignRecipientSerializer,
    CampaignEventSerializer, CampaignPropensityScoreSerializer,
    AttributionTouchpointSerializer, LeadSerializer, CampaignTransactionSerializer
)
from .services import CampaignExecutionService
from .tasks import execute_campaign
from .ai.bandit import ThompsonSamplingBandit
from .ai.audience_agent import AutonomousAudienceAgent
from .ai.attribution import AttributionCalculator
from .ai.narrator import AttributionNarrator
from intelligence.llm_client import LLMClient


class StandardPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'

    def paginate_queryset(self, queryset, request, view=None):
        if 'page' not in request.query_params and 'page_size' not in request.query_params:
            return None
        return super().paginate_queryset(queryset, request, view=view)


class CampaignViewSet(viewsets.ModelViewSet):
    serializer_class = CampaignSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        user = self.request.user
        company = getattr(user.profile, 'company', None) if hasattr(user, 'profile') else None
        if not company:
            return Campaign.objects.none()
        return Campaign.objects.filter(company=company).prefetch_related('contents', 'campaign_segments__segment').order_by('-created_at')

    def perform_create(self, serializer):
        company = self.request.user.profile.company
        campaign = serializer.save(company=company)

        # Create default content variant if none provided
        CampaignContent.objects.create(
            campaign=campaign,
            variant_name='A',
            subject=f"Special Announcement: {campaign.name}",
            body_html=f"<h2>Hello {{{{ customer.name }}}},</h2><p>We are thrilled to share an exclusive update with you.</p>",
            body_plain=f"Hello {{{{ customer.name }}}},\n\nWe are thrilled to share an exclusive update with you.",
            message_text=f"Hello {{{{ customer.name }}}}, check out our latest update: {campaign.name}",
            cta_text="Learn More",
            cta_url="https://horizon360.ai"
        )

        RawEvent.objects.create(
            company=company,
            event_name='campaign.created',
            raw_payload={"campaign_id": campaign.id, "name": campaign.name, "status": campaign.status},
            processed=False
        )

    def perform_update(self, serializer):
        old_status = serializer.instance.status
        campaign = serializer.save()

        if old_status != campaign.status:
            RawEvent.objects.create(
                company=campaign.company,
                event_name=f'campaign.{campaign.status}',
                raw_payload={"campaign_id": campaign.id, "name": campaign.name, "status": campaign.status},
                processed=False
            )

    @action(detail=True, methods=['post'], url_path='preview-audience')
    def preview_audience(self, request, pk=None):
        """
        Evaluates the campaign's segments, consent, and channel gate,
        returning real-time resolved audience count and diagnostics.
        """
        campaign = self.get_object()
        service = CampaignExecutionService()
        audience = service.resolve_audience(campaign)

        campaign.estimated_audience = len(audience)
        campaign.save(update_fields=['estimated_audience'])

        # Detailed breakdown
        total_customers = Customer.objects.filter(company=campaign.company).count()
        consented_count = sum(1 for c in audience if getattr(getattr(c, 'unified_profile', None), 'marketing_consent', False))

        return Response({
            "campaign_id": campaign.id,
            "estimated_audience": len(audience),
            "total_company_customers": total_customers,
            "consented_recipients": consented_count or len(audience),
            "channel": campaign.channel,
            "sample_recipients": [
                {
                    "id": str(c.id),
                    "email": c.primary_email,
                    "phone": c.primary_phone,
                    "account": c.account.name if c.account else None
                }
                for c in audience[:5]
            ]
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='send-now')
    def send_now(self, request, pk=None):
        """
        Triggers immediate execution of the campaign via Celery (or synchronous fallback).
        """
        campaign = self.get_object()
        if campaign.status in ['sending', 'completed']:
            return Response({"error": f"Campaign is already {campaign.status}"}, status=status.HTTP_400_BAD_REQUEST)

        campaign.status = 'sending'
        campaign.started_at = timezone.now()
        campaign.save(update_fields=['status', 'started_at'])

        try:
            # Trigger Celery async task
            execute_campaign.delay(campaign.id)
        except Exception:
            # Synchronous execution fallback if Celery/Redis is not running
            execute_campaign(campaign.id)

        return Response({
            "status": "success",
            "message": f"Campaign '{campaign.name}' execution dispatched.",
            "campaign_status": campaign.status
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['post'], url_path='schedule')
    def schedule(self, request, pk=None):
        """
        Schedules campaign for a specified future send datetime.
        """
        campaign = self.get_object()
        scheduled_at = request.data.get('scheduled_at')
        tz = request.data.get('timezone', 'UTC')

        if not scheduled_at:
            return Response({"error": "scheduled_at datetime is required"}, status=status.HTTP_400_BAD_REQUEST)

        campaign.scheduled_at = scheduled_at
        campaign.timezone = tz
        campaign.status = 'scheduled'
        campaign.save(update_fields=['scheduled_at', 'timezone', 'status'])

        CampaignExecutionService().emit_campaign_lifecycle_event(
            campaign, 'campaign.scheduled', {'scheduled_at': scheduled_at, 'timezone': tz}
        )

        return Response({
            "status": "scheduled",
            "campaign_id": campaign.id,
            "scheduled_at": campaign.scheduled_at,
            "timezone": campaign.timezone
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='pause')
    def pause(self, request, pk=None):
        campaign = self.get_object()
        campaign.status = 'paused'
        campaign.save(update_fields=['status'])
        CampaignExecutionService().emit_campaign_lifecycle_event(campaign, 'campaign.paused')
        return Response({"status": "paused", "campaign_id": campaign.id}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='resume')
    def resume(self, request, pk=None):
        campaign = self.get_object()
        campaign.status = 'active'
        campaign.save(update_fields=['status'])
        CampaignExecutionService().emit_campaign_lifecycle_event(campaign, 'campaign.resumed')
        return Response({"status": "active", "campaign_id": campaign.id}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='duplicate')
    def duplicate(self, request, pk=None):
        """
        Clones a campaign and its content variants into a new draft.
        """
        original = self.get_object()
        new_campaign = Campaign.objects.create(
            company=original.company,
            name=f"Copy of {original.name}",
            description=original.description,
            channel=original.channel,
            campaign_type=original.campaign_type,
            budget=original.budget,
            goal_event=original.goal_event,
            goal_value=original.goal_value,
            bandit_enabled=original.bandit_enabled,
            bandit_metric=original.bandit_metric,
            sender_name=original.sender_name,
            sender_email=original.sender_email,
            reply_to=original.reply_to,
            ai_audience_enabled=original.ai_audience_enabled,
            ai_copy_enabled=original.ai_copy_enabled,
            ai_send_time_enabled=original.ai_send_time_enabled,
            status='draft'
        )

        # Clone segments
        for cs in original.campaign_segments.all():
            CampaignSegment.objects.create(
                campaign=new_campaign,
                segment=cs.segment,
                is_exclusion=cs.is_exclusion
            )

        # Clone contents
        for c in original.contents.all():
            CampaignContent.objects.create(
                campaign=new_campaign,
                variant_name=c.variant_name,
                subject=c.subject,
                preview_text=c.preview_text,
                body_html=c.body_html,
                body_plain=c.body_plain,
                message_text=c.message_text,
                cta_url=c.cta_url,
                cta_text=c.cta_text,
                traffic_percentage=c.traffic_percentage
            )

        return Response(CampaignSerializer(new_campaign).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='analytics')
    def analytics(self, request, pk=None):
        """
        Returns full multi-channel campaign analytics, bandit variant allocations,
        attribution breakdowns, and funnel conversion rates.
        """
        campaign = self.get_object()
        contents = list(campaign.contents.all())

        # Bandit distribution
        bandit = ThompsonSamplingBandit()
        bandit_stats = bandit.get_distribution_stats(contents) if contents else []

        # Channel breakdown from attribution
        channel_data = AttributionCalculator.get_campaign_channel_breakdown(campaign)

        # Financial totals
        spend_txs = campaign.transactions.filter(transaction_type='spend')
        roi_txs = campaign.transactions.filter(transaction_type='roi')
        total_spend = sum(float(t.amount) for t in spend_txs) or float(campaign.budget or 0)
        total_roi = sum(float(t.amount) for t in roi_txs) or float(campaign.goal_value or 0)
        roi_percentage = round(((total_roi - total_spend) / total_spend * 100), 1) if total_spend > 0 else 0.0

        delivered = campaign.total_delivered or 0
        sent = campaign.total_sent or 0

        funnel = [
            {"stage": "Audience Targeted", "count": campaign.estimated_audience or sent},
            {"stage": "Sent", "count": sent},
            {"stage": "Delivered", "count": delivered},
            {"stage": "Opened", "count": campaign.total_opened},
            {"stage": "Clicked", "count": campaign.total_clicked},
            {"stage": "Converted", "count": campaign.total_converted},
        ]

        return Response({
            "campaign_id": campaign.id,
            "name": campaign.name,
            "status": campaign.status,
            "channel": campaign.channel,
            "funnel": funnel,
            "kpis": {
                "sent": sent,
                "delivered": delivered,
                "opened": campaign.total_opened,
                "clicked": campaign.total_clicked,
                "converted": campaign.total_converted,
                "bounced": campaign.total_bounced,
                "unsubscribed": campaign.total_unsubscribed,
                "open_rate": round((campaign.total_opened / delivered * 100), 1) if delivered > 0 else 0.0,
                "click_rate": round((campaign.total_clicked / delivered * 100), 1) if delivered > 0 else 0.0,
                "conversion_rate": round((campaign.total_converted / max(sent, 1) * 100), 1),
                "delivery_rate": round((delivered / max(sent, 1) * 100), 1),
            },
            "financials": {
                "spend": total_spend,
                "roi": total_roi,
                "net_profit": total_roi - total_spend,
                "roi_percentage": roi_percentage,
            },
            "bandit_variants": bandit_stats,
            "channel_attribution": channel_data,
            "propensity": {
                "average_score": campaign.avg_propensity_score,
                "churn_risk_count": campaign.churn_risk_count
            }
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='generate-audience')
    def generate_audience(self, request, pk=None):
        """
        Autonomous Audience Segmentation Agent:
        Analyzes historical UDM successes and outputs dynamic lookalike segment rules.
        """
        campaign = self.get_object()
        agent = AutonomousAudienceAgent()
        rules, rationale = agent.generate_lookalike_rules(
            company=campaign.company,
            campaign_name=campaign.name,
            channel=campaign.channel,
            goal_description=campaign.description or "High conversion"
        )
        estimated_size = agent.estimate_audience_size(campaign.company, rules)

        # Optionally save as a new Segment if requested
        save_as_segment = request.data.get('save_as_segment', False)
        created_segment_id = None
        if save_as_segment and rules:
            segment = Segment.objects.create(
                company=campaign.company,
                name=f"Lookalike: {campaign.name}",
                description=rationale,
                rules=rules,
                is_active=True
            )
            CampaignSegment.objects.create(campaign=campaign, segment=segment)
            created_segment_id = str(segment.id)

        return Response({
            "status": "success",
            "campaign_id": campaign.id,
            "rationale": rationale,
            "recommended_rules": rules,
            "estimated_audience_size": estimated_size,
            "created_segment_id": created_segment_id,
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='generate-copy')
    def generate_copy(self, request, pk=None):
        """
        Retrieval-Augmented Copy Generation:
        Generates personalized copy variants grounded in brand tone and goal.
        """
        campaign = self.get_object()
        tone = request.data.get('tone', 'persuasive and professional')
        variant_name = request.data.get('variant_name', f"Variant {campaign.contents.count() + 1}")
        custom_instructions = request.data.get('instructions', '')

        llm = LLMClient()
        system_prompt = (
            "You are an elite B2B and consumer copywriter for Horizon360 Marketing BIOM. "
            "Generate high-converting campaign copy adhering to best practices. "
            "Support dynamic merge tags like {{ customer.name }} and {{ account.name }}. "
            "Return valid JSON containing: 'subject', 'preview_text', 'body_html', 'body_plain', 'message_text', 'cta_text'."
        )
        user_prompt = (
            f"Campaign: '{campaign.name}' on channel '{campaign.channel}'.\n"
            f"Goal: {campaign.goal_event or 'engagement'}. Tone: {tone}.\n"
            f"Description / Context: {campaign.description}\n"
            f"Additional Instructions: {custom_instructions}\n"
            "Generate the creative variant now."
        )

        resp = llm.chat_completion(
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0.7
        )

        content_text = resp.get('content', '')
        copy_data = {}
        try:
            if '```json' in content_text:
                json_str = content_text.split('```json', 1)[1].split('```', 1)[0].strip()
            elif '```' in content_text:
                json_str = content_text.split('```', 1)[1].split('```', 1)[0].strip()
            else:
                json_str = content_text.strip()
            copy_data = json.loads(json_str)
        except Exception:
            copy_data = {
                "subject": f"Transform your operations with {campaign.name}",
                "preview_text": "Discover what is possible with Horizon360.",
                "body_html": f"<p>Hi {{{{ customer.name }}}},</p><p>We noticed your interest in scaling operations. Learn how {campaign.name} accelerates your success.</p>",
                "body_plain": f"Hi {{{{ customer.name }}}},\n\nWe noticed your interest in scaling operations. Learn how {campaign.name} accelerates your success.",
                "message_text": f"Hi {{{{ customer.name }}}}, check out {campaign.name}: https://horizon360.ai",
                "cta_text": "Explore Now"
            }

        # Save new variant to campaign
        created_content = CampaignContent.objects.create(
            campaign=campaign,
            variant_name=variant_name,
            subject=copy_data.get('subject', ''),
            preview_text=copy_data.get('preview_text', ''),
            body_html=copy_data.get('body_html', ''),
            body_plain=copy_data.get('body_plain', ''),
            message_text=copy_data.get('message_text', ''),
            cta_text=copy_data.get('cta_text', 'Learn More'),
            cta_url="https://horizon360.ai",
            ai_generated=True,
            ai_generation_prompt=user_prompt[:500]
        )

        return Response(CampaignContentSerializer(created_content).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='attribution-briefing')
    def attribution_briefing(self, request, pk=None):
        """
        Attribution Insight Narration:
        Returns LLM-reasoned narrative executive briefing on multi-touch channel efficiency.
        """
        campaign = self.get_object()
        narrator = AttributionNarrator()
        briefing = narrator.generate_briefing(campaign)
        return Response(briefing, status=status.HTTP_200_OK)


class CampaignContentViewSet(viewsets.ModelViewSet):
    serializer_class = CampaignContentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        company = getattr(user.profile, 'company', None) if hasattr(user, 'profile') else None
        if not company:
            return CampaignContent.objects.none()
        campaign_id = self.request.query_params.get('campaign')
        qs = CampaignContent.objects.filter(campaign__company=company)
        if campaign_id:
            qs = qs.filter(campaign_id=campaign_id)
        return qs

    @action(detail=True, methods=['post'], url_path='preview')
    def preview(self, request, pk=None):
        content = self.get_object()
        customer_id = request.data.get('customer_id')
        service = CampaignExecutionService()

        customer = None
        if customer_id:
            customer = Customer.objects.filter(id=customer_id, company=content.campaign.company).first()
        if not customer:
            customer = Customer.objects.filter(company=content.campaign.company).first()

        if not customer:
            return Response({"error": "No customer available for sample preview"}, status=status.HTTP_400_BAD_REQUEST)

        rendered = service.render_content(content, customer)
        return Response({
            "variant_name": content.variant_name,
            "sample_customer": customer.primary_email or str(customer.id),
            "rendered": rendered
        }, status=status.HTTP_200_OK)


class CampaignRecipientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CampaignRecipientSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        user = self.request.user
        company = getattr(user.profile, 'company', None) if hasattr(user, 'profile') else None
        if not company:
            return CampaignRecipient.objects.none()

        qs = CampaignRecipient.objects.filter(company=company).select_related('customer', 'content_variant', 'campaign')
        campaign_id = self.request.query_params.get('campaign')
        if campaign_id:
            qs = qs.filter(campaign_id=campaign_id)
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        return qs.order_by('-queued_at')


class CampaignEventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CampaignEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        user = self.request.user
        company = getattr(user.profile, 'company', None) if hasattr(user, 'profile') else None
        if not company:
            return CampaignEvent.objects.none()

        qs = CampaignEvent.objects.filter(company=company).select_related('campaign', 'recipient__customer')
        campaign_id = self.request.query_params.get('campaign')
        if campaign_id:
            qs = qs.filter(campaign_id=campaign_id)
        return qs.order_by('-created_at')


class AttributionTouchpointViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AttributionTouchpointSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        user = self.request.user
        company = getattr(user.profile, 'company', None) if hasattr(user, 'profile') else None
        if not company:
            return AttributionTouchpoint.objects.none()

        qs = AttributionTouchpoint.objects.filter(company=company).select_related('campaign', 'customer')
        campaign_id = self.request.query_params.get('campaign')
        if campaign_id:
            qs = qs.filter(campaign_id=campaign_id)
        return qs.order_by('-occurred_at')


class TemplateViewSet(viewsets.ModelViewSet):
    serializer_class = CampaignContentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        company = getattr(user.profile, 'company', None) if hasattr(user, 'profile') else None
        if not company:
            return CampaignContent.objects.none()
        return CampaignContent.objects.filter(campaign__company=company, is_template=True).order_by('-updated_at')


class MarketingDashboardView(APIView):
    """
    Comprehensive Marketing BIOM aggregated KPIs across campaigns, leads, and spend.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        company = request.user.profile.company
        campaigns = Campaign.objects.filter(company=company)
        leads = Lead.objects.filter(company=company)
        transactions = CampaignTransaction.objects.filter(company=company)

        active_campaigns = campaigns.filter(status='active').count()
        total_budget = sum(float(c.budget or 0) for c in campaigns.filter(status__in=['active', 'scheduled']))

        total_leads = leads.count()
        converted_leads = leads.filter(status='converted').count()
        conversion_rate = round((converted_leads / total_leads * 100), 1) if total_leads > 0 else 0.0

        total_spend = sum(float(t.amount) for t in transactions.filter(transaction_type='spend'))
        total_roi = sum(float(t.amount) for t in transactions.filter(transaction_type='roi'))

        return Response({
            "active_campaigns_count": active_campaigns,
            "total_campaigns_count": campaigns.count(),
            "active_budget": total_budget,
            "total_leads": total_leads,
            "converted_leads": converted_leads,
            "conversion_rate": conversion_rate,
            "total_spend": total_spend,
            "total_attributed_roi": total_roi,
            "net_roi_percentage": round(((total_roi - total_spend) / total_spend * 100), 1) if total_spend > 0 else 0.0
        }, status=status.HTTP_200_OK)


class LeadViewSet(viewsets.ModelViewSet):
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Lead.objects.filter(company=self.request.user.profile.company).select_related('customer', 'campaign')

    def perform_create(self, serializer):
        lead = serializer.save(company=self.request.user.profile.company)
        RawEvent.objects.create(
            company=lead.company,
            customer=lead.customer,
            event_name='lead.created',
            raw_payload={"lead_id": lead.id, "name": lead.name, "email": lead.email},
            processed=False
        )
        if lead.status == 'qualified':
            RawEvent.objects.create(
                company=lead.company,
                customer=lead.customer,
                event_name='lead.qualified',
                raw_payload={"lead_id": lead.id, "name": lead.name},
                processed=False
            )
        elif lead.status == 'converted':
            RawEvent.objects.create(
                company=lead.company,
                customer=lead.customer,
                event_name='lead.converted',
                raw_payload={"lead_id": lead.id, "name": lead.name},
                processed=False
            )

    def perform_update(self, serializer):
        old_status = serializer.instance.status
        lead = serializer.save()

        if old_status != lead.status:
            if lead.status == 'qualified':
                RawEvent.objects.create(
                    company=lead.company,
                    customer=lead.customer,
                    event_name='lead.qualified',
                    raw_payload={"lead_id": lead.id, "name": lead.name},
                    processed=False
                )
            elif lead.status == 'converted':
                RawEvent.objects.create(
                    company=lead.company,
                    customer=lead.customer,
                    event_name='lead.converted',
                    raw_payload={"lead_id": lead.id, "name": lead.name},
                    processed=False
                )


class CampaignTransactionPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'


class CampaignTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = CampaignTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CampaignTransactionPagination

    def get_queryset(self):
        return CampaignTransaction.objects.filter(company=self.request.user.profile.company).select_related('campaign')

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.profile.company)
