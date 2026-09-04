from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from crm.models import Deal, Activity
from finance.models import Invoice, Transaction, JournalEntry
from projects.models import Project
from service.models import ServiceTicket


class OrchestrationStatusView(APIView):
    """
    GET  ?deal_id=<id>  — Returns orchestration artefacts for the given deal.
    POST {deal_id: <id>} — Manually triggers deal-won orchestration.
    """

    def get(self, request):
        deal_id = request.query_params.get('deal_id')
        if not deal_id:
            return Response(
                {'error': 'deal_id query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            deal = Deal.objects.get(pk=deal_id)
        except Deal.DoesNotExist:
            return Response(
                {'error': f'Deal {deal_id} not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        invoices = Invoice.objects.filter(deal=deal).values(
            'id', 'invoice_number', 'amount', 'status', 'created_at',
        )
        project_name = f'Delivery: {deal.title}'
        projects = Project.objects.filter(
            company=deal.company, customer=deal.customer, name=project_name,
        ).values('id', 'name', 'status', 'created_at')

        ticket_title = f'Customer Onboarding: {deal.title}'
        tickets = ServiceTicket.objects.filter(
            company=deal.company, customer=deal.customer, title=ticket_title,
        ).values('id', 'title', 'status', 'priority', 'created_at')

        activities = Activity.objects.filter(
            deal=deal, activity_type='system',
        ).values('id', 'title', 'description', 'performed_at')

        orchestrated = bool(invoices) or bool(projects) or bool(tickets) or bool(activities)

        return Response({
            'deal_id': deal.id,
            'deal_title': deal.title,
            'deal_stage': deal.stage,
            'orchestrated': orchestrated,
            'finance': {
                'invoices': list(invoices),
            },
            'projects': list(projects),
            'service': {
                'tickets': list(tickets),
            },
            'hrms': {
                'activities': list(activities),
            },
        })

    def post(self, request):
        deal_id = request.data.get('deal_id')
        if not deal_id:
            return Response(
                {'error': 'deal_id is required in the request body.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            deal = Deal.objects.get(pk=deal_id)
        except Deal.DoesNotExist:
            return Response(
                {'error': f'Deal {deal_id} not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if deal.stage != 'won':
            return Response(
                {'error': f'Deal stage is "{deal.stage}". Orchestration requires stage "won".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from crm.tasks import run_deal_won_orchestration
        run_deal_won_orchestration.delay(deal.id)

        return Response(
            {'status': 'orchestration_triggered', 'deal_id': deal.id},
            status=status.HTTP_202_ACCEPTED,
        )
