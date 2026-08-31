from rest_framework import viewsets, permissions
from .models import Campaign, Lead
from .serializers import CampaignSerializer, LeadSerializer
from cdp_core.models import RawEvent

class CampaignViewSet(viewsets.ModelViewSet):
    serializer_class = CampaignSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Campaign.objects.filter(company=self.request.user.profile.company)

    def perform_create(self, serializer):
        campaign = serializer.save(company=self.request.user.profile.company)
        
        RawEvent.objects.create(
            company=campaign.company,
            event_name='campaign.created',
            raw_payload={"campaign_id": campaign.id, "name": campaign.name, "status": campaign.status},
            processed=False
        )
        if campaign.status == 'active':
            RawEvent.objects.create(
                company=campaign.company,
                event_name='campaign.activated',
                raw_payload={"campaign_id": campaign.id, "name": campaign.name},
                processed=False
            )

    def perform_update(self, serializer):
        old_status = serializer.instance.status
        campaign = serializer.save()
        
        if old_status != campaign.status and campaign.status == 'active':
            RawEvent.objects.create(
                company=campaign.company,
                event_name='campaign.activated',
                raw_payload={"campaign_id": campaign.id, "name": campaign.name},
                processed=False
            )


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
