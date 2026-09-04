import logging
from decimal import Decimal
from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)


def orchestrate_deal_won(deal_id):
    """
    Orchestrates cross-BIOM actions when a Deal is marked as 'won'.

    Creates:
      - Finance: Invoice, Transaction, and GL JournalEntry records
      - Projects: Project with default delivery Tasks
      - Service: Onboarding ServiceTicket
      - HRMS: Resource allocation Activity (system event)

    Idempotent — skips creation if records already exist for the deal.
    Returns a dict summarising all created (or existing) records.
    """
    from crm.models import Deal, Activity
    from finance.models import Invoice, Transaction, JournalEntry
    from projects.models import Project, Task
    from service.models import ServiceTicket

    deal = Deal.objects.select_related('company', 'customer').get(pk=deal_id)

    if deal.stage != 'won':
        logger.warning(
            f"Orchestration skipped: Deal {deal_id} stage is '{deal.stage}', not 'won'."
        )
        return {'status': 'skipped', 'reason': f'Deal stage is {deal.stage}'}

    results = {}

    with transaction.atomic():
        # ------------------------------------------------------------------ #
        # 1. Finance BIOM — Invoice, Transaction, JournalEntry
        # ------------------------------------------------------------------ #
        invoice, invoice_created = _create_invoice(deal)
        results['invoice'] = {
            'id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'created': invoice_created,
        }

        if invoice_created:
            txn = Transaction.objects.create(
                company=deal.company,
                transaction_type='earn',
                description=f'Revenue from Deal: {deal.title}',
                amount=deal.value,
            )
            results['transaction'] = {'id': str(txn.id), 'created': True}

            # Double-entry GL: debit Accounts Receivable, credit Revenue
            ar_entry = JournalEntry.objects.create(
                company=deal.company,
                entry_type='debit',
                account_code='1200_ACCOUNTS_RECEIVABLE',
                amount=deal.value,
                reference_type='invoice',
                reference_id=str(invoice.id),
                description=f'AR for Invoice {invoice.invoice_number} (Deal: {deal.title})',
            )
            rev_entry = JournalEntry.objects.create(
                company=deal.company,
                entry_type='credit',
                account_code='4000_REVENUE',
                amount=deal.value,
                reference_type='invoice',
                reference_id=str(invoice.id),
                description=f'Revenue for Invoice {invoice.invoice_number} (Deal: {deal.title})',
            )
            results['journal_entries'] = [
                {'id': str(ar_entry.id), 'type': 'debit'},
                {'id': str(rev_entry.id), 'type': 'credit'},
            ]
        else:
            results['transaction'] = {'created': False}
            results['journal_entries'] = []

        # ------------------------------------------------------------------ #
        # 2. Projects BIOM — Project + default Tasks
        # ------------------------------------------------------------------ #
        project, project_created = _create_project(deal)
        results['project'] = {
            'id': project.id,
            'name': project.name,
            'created': project_created,
        }

        if project_created:
            default_tasks = [
                'Kickoff & Requirements Gathering',
                'Implementation & Development',
                'Testing & QA',
            ]
            task_ids = []
            for task_title in default_tasks:
                task = Task.objects.create(
                    project=project,
                    title=task_title,
                    status='todo',
                )
                task_ids.append(task.id)
            results['tasks'] = {'ids': task_ids, 'created': True}
        else:
            results['tasks'] = {'created': False}

        # ------------------------------------------------------------------ #
        # 3. Service BIOM — Onboarding ServiceTicket
        # ------------------------------------------------------------------ #
        ticket, ticket_created = _create_service_ticket(deal)
        results['service_ticket'] = {
            'id': ticket.id,
            'title': ticket.title,
            'created': ticket_created,
        }

        # ------------------------------------------------------------------ #
        # 4. HRMS BIOM — Resource allocation Activity
        # ------------------------------------------------------------------ #
        activity, activity_created = _create_resource_activity(deal)
        results['activity'] = {
            'id': str(activity.id),
            'title': activity.title,
            'created': activity_created,
        }

    results['status'] = 'completed'
    logger.info(f"Orchestration completed for Deal {deal_id}: {results}")
    return results


# --------------------------------------------------------------------------- #
# Private helpers (idempotent)
# --------------------------------------------------------------------------- #

def _create_invoice(deal):
    """Return (invoice, created) — reuses existing invoice for the deal."""
    from finance.models import Invoice

    existing = Invoice.objects.filter(deal=deal).first()
    if existing:
        return existing, False

    now = timezone.now()
    invoice_number = f"INV-{deal.id}-{now.strftime('%Y%m%d%H%M%S')}"
    invoice = Invoice.objects.create(
        company=deal.company,
        customer=deal.customer,
        deal=deal,
        invoice_number=invoice_number,
        amount=deal.value,
        status='issued',
        issued_at=now,
    )
    return invoice, True


def _create_project(deal):
    """Return (project, created) — reuses existing delivery project for the deal."""
    from projects.models import Project

    project_name = f'Delivery: {deal.title}'
    existing = Project.objects.filter(
        company=deal.company,
        customer=deal.customer,
        name=project_name,
    ).first()
    if existing:
        return existing, False

    project = Project.objects.create(
        company=deal.company,
        customer=deal.customer,
        name=project_name,
        status='planned',
    )
    return project, True


def _create_service_ticket(deal):
    """Return (ticket, created) — reuses existing onboarding ticket for the deal."""
    from service.models import ServiceTicket

    ticket_title = f'Customer Onboarding: {deal.title}'
    existing = ServiceTicket.objects.filter(
        company=deal.company,
        customer=deal.customer,
        title=ticket_title,
    ).first()
    if existing:
        return existing, False

    ticket = ServiceTicket.objects.create(
        company=deal.company,
        customer=deal.customer,
        title=ticket_title,
        description=(
            f'Automated onboarding ticket created from closed deal. '
            f'Deal Value: ${deal.value}'
        ),
        status='open',
        priority='high',
    )
    return ticket, True


def _create_resource_activity(deal):
    """Return (activity, created) — reuses existing system activity for the deal."""
    from crm.models import Activity

    activity_title = f'Resource Allocation Required: {deal.title}'
    existing = Activity.objects.filter(
        company=deal.company,
        deal=deal,
        activity_type='system',
        title=activity_title,
    ).first()
    if existing:
        return existing, False

    activity = Activity.objects.create(
        company=deal.company,
        customer=deal.customer,
        deal=deal,
        activity_type='system',
        title=activity_title,
        description=(
            f'Deal {deal.title} has been won (${deal.value}). '
            f'Team allocation needed for delivery project.'
        ),
    )
    return activity, True
