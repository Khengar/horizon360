import logging
from typing import Dict, Any, List
from django.db.models import Q
from cdp_core.models import Company, Account, Customer
from .models import Contact, Deal, Quote

logger = logging.getLogger(__name__)

def perform_universal_search(company: Company, query_text: str, limit: int = 10) -> Dict[str, Any]:
    """
    Executes a multi-entity cross-BIOM search scoped to the given tenant.
    Searches Accounts, Contacts, Customers, Deals, Quotes, Invoices, and Service Tickets.
    """
    if not query_text or not isinstance(query_text, str):
        return {"query": "", "total_matches": 0, "results": {}}

    q_clean = query_text.strip()
    results = {}
    total_count = 0

    # 1. Accounts
    accounts = Account.objects.filter(
        Q(company=company) & 
        (Q(name__icontains=q_clean) | Q(domain__icontains=q_clean) | Q(industry__icontains=q_clean))
    )[:limit]
    results['accounts'] = [
        {"id": str(a.id), "name": a.name, "domain": a.domain, "tier": a.tier, "industry": a.industry}
        for a in accounts
    ]
    total_count += len(results['accounts'])

    # 2. Customers
    customers = Customer.objects.filter(
        Q(company=company) & 
        (Q(primary_email__icontains=q_clean) | Q(primary_phone__icontains=q_clean))
    )[:limit]
    results['customers'] = [
        {"id": str(c.id), "email": c.primary_email, "phone": c.primary_phone, "account_name": c.account.name if c.account else None}
        for c in customers
    ]
    total_count += len(results['customers'])

    # 3. Contacts
    contacts = Contact.objects.filter(
        Q(company=company) & 
        (Q(notes__icontains=q_clean) | Q(customer__primary_email__icontains=q_clean) | Q(customer__primary_phone__icontains=q_clean))
    ).select_related('customer', 'account')[:limit]
    results['contacts'] = [
        {"id": c.id, "email": c.primary_email, "phone": c.primary_phone, "account_name": c.account.name if c.account else None, "notes": c.notes[:100]}
        for c in contacts
    ]
    total_count += len(results['contacts'])

    # 4. Deals
    deals = Deal.objects.filter(
        Q(company=company) & 
        (Q(title__icontains=q_clean) | Q(stage__icontains=q_clean) | Q(account__name__icontains=q_clean) | Q(customer__primary_email__icontains=q_clean))
    ).select_related('account', 'customer')[:limit]
    results['deals'] = [
        {"id": d.id, "title": d.title, "stage": d.stage, "value": float(d.value), "probability": d.probability, "account_name": d.account.name if d.account else None}
        for d in deals
    ]
    total_count += len(results['deals'])

    # 5. Quotes
    quotes = Quote.objects.filter(
        Q(company=company) & 
        (Q(quote_number__icontains=q_clean) | Q(notes__icontains=q_clean) | Q(deal__title__icontains=q_clean) | Q(account__name__icontains=q_clean) | Q(customer__primary_email__icontains=q_clean))
    ).select_related('deal', 'account', 'customer')[:limit]
    results['quotes'] = [
        {"id": str(q.id), "quote_number": q.quote_number, "status": q.status, "total_amount": float(q.total_amount), "deal_title": q.deal.title if q.deal else None}
        for q in quotes
    ]
    total_count += len(results['quotes'])

    # 6. Invoices
    try:
        from finance.models import Invoice
        invoices = Invoice.objects.filter(
            Q(company=company) & 
            (Q(invoice_number__icontains=q_clean) | Q(status__icontains=q_clean) | Q(customer__primary_email__icontains=q_clean) | Q(deal__title__icontains=q_clean))
        ).select_related('customer', 'deal')[:limit]
        results['invoices'] = [
            {"id": inv.id, "invoice_number": inv.invoice_number, "status": inv.status, "amount": float(inv.amount)}
            for inv in invoices
        ]
        total_count += len(results['invoices'])
    except Exception:
        results['invoices'] = []

    # 7. Service Tickets
    try:
        from service.models import ServiceTicket
        tickets = ServiceTicket.objects.filter(
            Q(company=company) & 
            (Q(title__icontains=q_clean) | Q(description__icontains=q_clean) | Q(status__icontains=q_clean) | Q(customer__primary_email__icontains=q_clean))
        ).select_related('customer')[:limit]
        results['tickets'] = [
            {"id": t.id, "title": t.title, "status": t.status, "priority": t.priority}
            for t in tickets
        ]
        total_count += len(results['tickets'])
    except Exception:
        results['tickets'] = []

    return {
        "query": q_clean,
        "total_matches": total_count,
        "results": results
    }

