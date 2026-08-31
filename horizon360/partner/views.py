from rest_framework import viewsets, permissions
from .models import Partner, PartnerOpportunity
from .serializers import PartnerSerializer, PartnerOpportunitySerializer
from cdp_core.models import RawEvent

class PartnerViewSet(viewsets.ModelViewSet):
    serializer_class = PartnerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Partner.objects.filter(company=self.request.user.profile.company)

    def perform_create(self, serializer):
        partner = serializer.save(company=self.request.user.profile.company)
        RawEvent.objects.create(
            company=partner.company,
            customer=partner.customer,
            event_name='partner.created',
            raw_payload={"partner_id": partner.id, "name": partner.name, "status": partner.status},
            processed=False
        )

    def perform_update(self, serializer):
        partner = serializer.save()
        RawEvent.objects.create(
            company=partner.company,
            customer=partner.customer,
            event_name='partner.updated',
            raw_payload={"partner_id": partner.id, "name": partner.name, "status": partner.status},
            processed=False
        )

class PartnerOpportunityViewSet(viewsets.ModelViewSet):
    serializer_class = PartnerOpportunitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PartnerOpportunity.objects.filter(company=self.request.user.profile.company)

    def perform_create(self, serializer):
        opp = serializer.save(company=self.request.user.profile.company)
        RawEvent.objects.create(
            company=opp.company,
            customer=opp.customer,
            event_name='partner_opportunity.created',
            raw_payload={"opportunity_id": opp.id, "partner_id": opp.partner.id, "stage": opp.stage, "value": str(opp.value)},
            processed=False
        )

    def perform_update(self, serializer):
        opp = serializer.save()
        event_name = 'partner_opportunity.updated'
        if opp.stage == 'won':
            event_name = 'partner_opportunity.won'
        elif opp.stage == 'lost':
            event_name = 'partner_opportunity.lost'
            
        RawEvent.objects.create(
            company=opp.company,
            customer=opp.customer,
            event_name=event_name,
            raw_payload={"opportunity_id": opp.id, "partner_id": opp.partner.id, "stage": opp.stage, "value": str(opp.value)},
            processed=False
        )
