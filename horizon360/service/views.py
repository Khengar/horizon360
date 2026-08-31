from rest_framework import viewsets, permissions
from django.utils import timezone
from .models import ServiceTicket
from .serializers import ServiceTicketSerializer
from cdp_core.models import RawEvent

class ServiceTicketViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ServiceTicket.objects.filter(company=self.request.user.profile.company).select_related('customer')

    def perform_create(self, serializer):
        ticket = serializer.save(company=self.request.user.profile.company)
        # Emit event
        RawEvent.objects.create(
            company=ticket.company,
            customer=ticket.customer,
            event_name='ticket.created',
            raw_payload={"ticket_id": ticket.id, "title": ticket.title, "priority": ticket.priority},
            processed=False
        )

    def perform_update(self, serializer):
        old_status = serializer.instance.status
        old_priority = serializer.instance.priority
        
        ticket = serializer.save()
        
        events = []
        if old_status != ticket.status and ticket.status == 'resolved':
            ticket.resolved_at = timezone.now()
            ticket.save()
            events.append('ticket.resolved')
            
        if old_priority != ticket.priority:
            events.append('ticket.priority_changed')
            
        for event_name in events:
            RawEvent.objects.create(
                company=ticket.company,
                customer=ticket.customer,
                event_name=event_name,
                raw_payload={"ticket_id": ticket.id, "title": ticket.title, "priority": ticket.priority, "status": ticket.status},
                processed=False
            )
