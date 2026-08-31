from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Insight
from .serializers import InsightSerializer
from .agents import MeshRunner
from cdp_core.models import Customer, Company, UserProfile
from crm.models import Deal
import logging

logger = logging.getLogger(__name__)

def get_or_create_user_company(user):
    if hasattr(user, 'profile') and user.profile and user.profile.company:
        return user.profile.company
    company = Company.objects.first()
    if not company:
        company = Company.objects.create(name='Default Corp')
    if user and user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'company': company})
        if not profile.company:
            profile.company = company
            profile.save()
    return company

class InsightViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InsightSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Insight.objects.none()
            
        company = get_or_create_user_company(self.request.user)
        qs = Insight.objects.filter(company=company).order_by('-created_at')
        agent_type = self.request.query_params.get('agent_type')
        severity = self.request.query_params.get('severity')
        
        if agent_type:
            qs = qs.filter(agent_type=agent_type)
        if severity:
            qs = qs.filter(severity=severity)
            
        return qs


class RunMeshView(APIView):
    """
    Executes the Multi-Agent Intelligence Mesh for the user's company.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        company = get_or_create_user_company(request.user)
        result = MeshRunner.run_mesh_for_company(company)
        
        # Return updated insights
        latest_insights = Insight.objects.filter(company=company).order_by('-created_at')[:15]
        result['insights'] = InsightSerializer(latest_insights, many=True).data

        return Response(result, status=status.HTTP_200_OK)


class ExecuteActionView(APIView):
    """
    Executes an autonomous AI remediation action (tagging, email drafting, deal progression, insight dismissal).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        company = get_or_create_user_company(request.user)
        action_type = request.data.get('action_type')
        entity_type = request.data.get('entity_type')
        entity_id = request.data.get('entity_id')
        insight_id = request.data.get('insight_id')
        payload = request.data.get('payload', {})

        if not action_type:
            return Response({"error": "action_type is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Mark insight as actioned if insight_id is provided
        if insight_id:
            Insight.objects.filter(id=insight_id, company=company).update(status='actioned')

        if action_type == 'apply_tag':
            tag_name = payload.get('tag', 'AI_ACTIONED')
            if entity_type == 'customer' and entity_id:
                cust = Customer.objects.filter(id=entity_id, company=company).first()
                if cust:
                    if not isinstance(cust.attributes, dict):
                        cust.attributes = {}
                    tags = cust.attributes.get('tags', [])
                    if tag_name not in tags:
                        tags.append(tag_name)
                    cust.attributes['tags'] = tags
                    cust.save()
                    return Response({"status": "success", "message": f"Tag '{tag_name}' applied to Customer {cust.id}"})

        elif action_type == 'draft_email':
            if entity_type == 'customer' and entity_id:
                cust = Customer.objects.filter(id=entity_id, company=company).first()
                if cust:
                    ident = cust.primary_email or cust.primary_phone or 'Valued Customer'
                    draft = payload.get('message') or f"Hi {ident}, we wanted to reach out regarding your recent account updates and offer dedicated support."
                    if not isinstance(cust.attributes, dict):
                        cust.attributes = {}
                    cust.attributes['latest_ai_email_draft'] = draft
                    cust.save()
                    return Response({"status": "success", "message": "Outreach draft generated successfully", "draft": draft})

        elif action_type == 'advance_deal':
            if entity_id:
                deal = Deal.objects.filter(id=entity_id, company=company).first()
                if deal:
                    target_stage = payload.get('stage', 'proposal')
                    deal.stage = target_stage
                    deal.save()
                    return Response({"status": "success", "message": f"Deal '{deal.title}' advanced to '{target_stage}'"})

        elif action_type == 'dismiss_insight':
            if insight_id:
                Insight.objects.filter(id=insight_id, company=company).update(status='dismissed')
                return Response({"status": "success", "message": "Insight dismissed"})

        return Response({"status": "success", "message": f"Action '{action_type}' processed successfully"})
