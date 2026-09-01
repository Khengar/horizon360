import re
import logging
from typing import Optional, Dict, Any
from django.db import transaction
from django.contrib.auth.models import User
from .models import Customer, RawEvent, AuditLog, Company
from .audit import record_audit_log

logger = logging.getLogger(__name__)

def normalize_email(email: Optional[str]) -> Optional[str]:
    """
    Normalizes an email string:
    - Strips leading/trailing whitespace
    - Lowercases all characters
    - Returns None for empty / invalid strings
    """
    if not email or not isinstance(email, str):
        return None
    email_clean = email.strip().lower()
    if '@' not in email_clean:
        return None
    return email_clean


def normalize_phone(phone: Optional[str]) -> Optional[str]:
    """
    Normalizes a phone number string:
    - Strips whitespace, dashes, parentheses, dots
    - Retains leading '+' for international standard (E.164-like)
    - Returns None if empty or fewer than 5 digits
    """
    if not phone or not isinstance(phone, str):
        return None
    phone_clean = phone.strip()
    has_plus = phone_clean.startswith('+')
    digits = re.sub(r'\D', '', phone_clean)
    if len(digits) < 5:
        return None
    return f"+{digits}" if has_plus else digits


def merge_customers(
    primary_customer: Customer,
    secondary_customer: Customer,
    user: Optional[User] = None
) -> Dict[str, Any]:
    """
    Merges a secondary Customer into a primary Customer within the same tenant.
    - Re-points all relational nodes (Deals, Invoices, ServiceTickets, Orders, Projects, Leads, RawEvents)
    - Merges attributes (primary takes precedence, fills missing keys from secondary)
    - Merges consent flags
    - Combines timelines chronologically
    - Deletes the secondary customer
    - Records an immutable AuditLog entry
    """
    if primary_customer.company_id != secondary_customer.company_id:
        raise ValueError("Cannot merge customers from different companies / tenants.")

    if primary_customer.id == secondary_customer.id:
        raise ValueError("Cannot merge a customer into itself.")

    company = primary_customer.company
    secondary_id_str = str(secondary_customer.id)
    primary_id_str = str(primary_customer.id)

    with transaction.atomic():
        # 1. Merge Attributes
        secondary_attrs = secondary_customer.attributes or {}
        primary_attrs = primary_customer.attributes or {}
        merged_attrs = {**secondary_attrs, **primary_attrs}

        # 2. Merge Consent
        secondary_consent = secondary_customer.consent or {}
        primary_consent = primary_customer.consent or {}
        merged_consent = {**secondary_consent, **primary_consent}

        # 3. Merge Timeline
        secondary_timeline = secondary_customer.timeline or []
        primary_timeline = primary_customer.timeline or []
        merged_timeline = list(primary_timeline) + list(secondary_timeline)
        # Sort timeline by received_at if available
        def get_event_time(item):
            if isinstance(item, dict):
                return item.get('received_at') or item.get('timestamp') or ''
            return ''
        merged_timeline.sort(key=get_event_time)

        # 4. Fill Primary Identifiers if missing on primary
        if not primary_customer.primary_email and secondary_customer.primary_email:
            primary_customer.primary_email = secondary_customer.primary_email
        if not primary_customer.primary_phone and secondary_customer.primary_phone:
            primary_customer.primary_phone = secondary_customer.primary_phone
        if not primary_customer.account_id and secondary_customer.account_id:
            primary_customer.account = secondary_customer.account

        primary_customer.attributes = merged_attrs
        primary_customer.consent = merged_consent
        primary_customer.timeline = merged_timeline

        # 5. Re-link all related models across all BIOMs
        # Raw Events
        raw_events_count = RawEvent.objects.filter(customer=secondary_customer).update(customer=primary_customer)

        # CRM Deals
        from crm.models import Deal, Contact
        deals_count = Deal.objects.filter(customer=secondary_customer).update(customer=primary_customer)
        
        # CRM Contacts - if secondary has a contact and primary doesn't, re-link; else update notes
        secondary_contacts = Contact.objects.filter(customer=secondary_customer)
        primary_contact = Contact.objects.filter(customer=primary_customer).first()
        for sec_contact in secondary_contacts:
            if not primary_contact:
                sec_contact.customer = primary_customer
                sec_contact.save()
                primary_contact = sec_contact
            else:
                if sec_contact.notes:
                    primary_contact.notes = f"{primary_contact.notes}\n[Merged Note]: {sec_contact.notes}".strip()
                    primary_contact.save()
                # Re-point deals attached to secondary contact to primary contact
                Deal.objects.filter(contact=sec_contact).update(contact=primary_contact)
                sec_contact.delete()

        # Finance Invoices
        try:
            from finance.models import Invoice
            invoices_count = Invoice.objects.filter(customer=secondary_customer).update(customer=primary_customer)
        except Exception:
            invoices_count = 0

        # Service Tickets
        try:
            from service.models import ServiceTicket
            tickets_count = ServiceTicket.objects.filter(customer=secondary_customer).update(customer=primary_customer)
        except Exception:
            tickets_count = 0

        # Commerce Orders
        try:
            from commerce.models import Order
            orders_count = Order.objects.filter(customer=secondary_customer).update(customer=primary_customer)
        except Exception:
            orders_count = 0

        # Projects
        try:
            from projects.models import Project
            projects_count = Project.objects.filter(customer=secondary_customer).update(customer=primary_customer)
        except Exception:
            projects_count = 0

        # Marketing Leads
        try:
            from marketing.models import Lead
            leads_count = Lead.objects.filter(customer=secondary_customer).update(customer=primary_customer)
        except Exception:
            leads_count = 0

        # Partner Opportunities
        try:
            from partner.models import PartnerOpportunity
            partner_opps_count = PartnerOpportunity.objects.filter(customer=secondary_customer).update(customer=primary_customer)
        except Exception:
            partner_opps_count = 0

        # Save Primary Customer
        primary_customer.save()

        # Capture secondary state snapshot for audit
        secondary_snapshot = {
            "id": secondary_id_str,
            "primary_email": secondary_customer.primary_email,
            "primary_phone": secondary_customer.primary_phone,
            "attributes": secondary_customer.attributes,
            "relinked": {
                "raw_events": raw_events_count,
                "deals": deals_count,
                "invoices": invoices_count,
                "tickets": tickets_count,
                "orders": orders_count,
                "projects": projects_count,
                "leads": leads_count,
                "partner_opportunities": partner_opps_count
            }
        }

        # Delete secondary customer
        secondary_customer.delete()

        # Record Audit Log
        record_audit_log(
            company=company,
            action='merge',
            entity_type='Customer',
            entity_id=primary_id_str,
            user=user,
            diff={
                "merged_secondary_customer": secondary_snapshot,
                "resulting_primary_customer_id": primary_id_str
            }
        )

        return {
            "status": "success",
            "primary_customer_id": primary_id_str,
            "merged_secondary_id": secondary_id_str,
            "relinked_entities": secondary_snapshot["relinked"]
        }
