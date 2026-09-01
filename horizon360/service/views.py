from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import ServiceTicket, SLAPolicy, TicketComment, KnowledgeArticle
from .serializers import (
    ServiceTicketSerializer, SLAPolicySerializer, 
    TicketCommentSerializer, KnowledgeArticleSerializer
)
from cdp_core.models import RawEvent
from cdp_core.audit import AuditLoggingMixin
from cdp_core.idempotency import IdempotencyMixin

class SLAPolicyViewSet(IdempotencyMixin, AuditLoggingMixin, viewsets.ModelViewSet):
    serializer_class = SLAPolicySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SLAPolicy.objects.filter(company=self.request.user.profile.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.profile.company)
        super().perform_create(serializer)


class ServiceTicketViewSet(IdempotencyMixin, AuditLoggingMixin, viewsets.ModelViewSet):
    serializer_class = ServiceTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ServiceTicket.objects.filter(company=self.request.user.profile.company).select_related('customer', 'sla_policy').prefetch_related('comments')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        priority_filter = self.request.query_params.get('priority')
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        customer_id = self.request.query_params.get('customer')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        return queryset

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
        super().perform_create(serializer)

    def perform_update(self, serializer):
        old_status = serializer.instance.status
        old_priority = serializer.instance.priority
        
        ticket = serializer.save()
        
        events = []
        if old_status != ticket.status and ticket.status == 'resolved':
            ticket.resolved_at = timezone.now()
            ticket.save(update_fields=['resolved_at'])
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
        super().perform_update(serializer)

    @action(detail=True, methods=['post'], url_path='add-comment')
    def add_comment(self, request, pk=None):
        ticket = self.get_object()
        serializer = TicketCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(ticket=ticket, author=request.user)
        ticket.refresh_from_db()
        return Response(TicketCommentSerializer(comment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='check-sla')
    def check_sla(self, request, pk=None):
        ticket = self.get_object()
        breached = ticket.check_sla_status()
        if breached:
            ticket.save(update_fields=['is_sla_breached'])
        return Response({
            "ticket_id": ticket.id,
            "is_sla_breached": ticket.is_sla_breached,
            "sla_due_at": ticket.sla_due_at,
            "resolved_at": ticket.resolved_at
        }, status=status.HTTP_200_OK)


class KnowledgeArticleViewSet(IdempotencyMixin, AuditLoggingMixin, viewsets.ModelViewSet):
    serializer_class = KnowledgeArticleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = KnowledgeArticle.objects.filter(company=self.request.user.profile.company)
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(title__icontains=search_query)
        return queryset

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.profile.company)
        super().perform_create(serializer)

    @action(detail=True, methods=['post'], url_path='view')
    def record_view(self, request, pk=None):
        article = self.get_object()
        article.view_count += 1
        article.save(update_fields=['view_count'])
        return Response({"status": "view_recorded", "view_count": article.view_count}, status=status.HTTP_200_OK)

