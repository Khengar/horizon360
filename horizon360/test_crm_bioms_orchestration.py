import os
import django
import sys
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horizon360.settings')
django.setup()

from django.contrib.auth.models import User
from cdp_core.models import Company, Customer, Account, UserProfile
from crm.models import Deal, Contact, PipelineStage, Activity, Quote, QuoteItem
from finance.models import Invoice, Transaction, JournalEntry
from projects.models import Project, Task
from service.models import ServiceTicket
from crm.orchestration import orchestrate_deal_won
from rest_framework.test import APIRequestFactory, force_authenticate
from crm.api_orchestration import OrchestrationStatusView

def run_tests():
    print("=" * 70)
    print("HORIZON 360: LEVEL 3 CRM & LEVEL 4 BIOMS COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    passed = 0
    failed = 0

    def assert_test(condition, test_name, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f" [PASS] {test_name}" + (f" -> {detail}" if detail else ""))
        else:
            failed += 1
            print(f" [FAIL] {test_name}" + (f" -> {detail}" if detail else ""))

    # Setup core context
    company = Company.objects.first()
    if not company:
        company = Company.objects.create(name="Acme Global Corporation")
    admin_user = User.objects.filter(username="admin").first()

    # -------------------------------------------------------------
    # TEST 1: Level 3 Universal CRM - Customer, Contact, Account
    # -------------------------------------------------------------
    print("\n--- Phase 1: Level 3 Universal CRM Data Structures ---")
    customer, _ = Customer.objects.get_or_create(
        company=company,
        primary_email="sarah.connor@cyberdyne.io",
        defaults={
            "primary_phone": "+1-555-0199",
            "attributes": {"firstName": "Sarah", "lastName": "Connor", "title": "Head of Operations"}
        }
    )
    assert_test(customer.id is not None, "Customer entity created/loaded", f"ID: {customer.id}")

    account, _ = Account.objects.get_or_create(
        company=company,
        name="Cyberdyne Systems",
        defaults={"domain": "cyberdyne.io", "industry": "Robotics & Defense", "tier": "Tier 1"}
    )
    assert_test(account.name == "Cyberdyne Systems", "Account entity linked", f"Tier: {account.tier}")

    contact, _ = Contact.objects.get_or_create(
        company=company,
        customer=customer,
        defaults={"account": account, "notes": "Primary enterprise decision maker"}
    )
    assert_test(contact.primary_email == "sarah.connor@cyberdyne.io", "Contact entity synchronization", f"Email: {contact.primary_email}")

    # -------------------------------------------------------------
    # TEST 2: Sales BIOM - Deal Lifecycle & Pipeline
    # -------------------------------------------------------------
    print("\n--- Phase 2: Sales BIOM & Pipeline Tracking ---")
    deal, _ = Deal.objects.get_or_create(
        company=company,
        title="Cyberdyne Neural Mesh Enterprise Contract",
        defaults={
            "customer": customer,
            "account": account,
            "contact": contact,
            "value": Decimal("125000.00"),
            "stage": "proposal",
            "probability": 60
        }
    )
    assert_test(deal.value == Decimal("125000.00"), "Deal creation with monetary valuation", f"${deal.value}")
    assert_test(deal.stage == "proposal", "Deal stage initialized", deal.stage)

    # -------------------------------------------------------------
    # TEST 3: Trigger Cross-BIOM Automated Business Orchestration
    # -------------------------------------------------------------
    print("\n--- Phase 3: Automated Cross-BIOM Orchestration (Deal Won) ---")
    # Transition deal to won
    deal.stage = "won"
    deal.save()
    assert_test(deal.stage == "won", "Deal transitioned to 'won' stage")
    assert_test(deal.probability == 100, "Deal probability automatically updated to 100%")
    assert_test(deal.forecast_category == "closed", "Deal forecast category updated to 'closed'")

    # Execute business orchestration
    orch_result = orchestrate_deal_won(deal.id)
    assert_test(orch_result is not None, "Business Orchestration executed successfully")
    assert_test(orch_result.get("status") == "completed", "Orchestration status marked 'completed'")

    # -------------------------------------------------------------
    # TEST 4: Finance BIOM - Invoicing & General Ledger
    # -------------------------------------------------------------
    print("\n--- Phase 4: Finance BIOM Auto-Provisioning ---")
    invoice = Invoice.objects.filter(deal=deal).first()
    assert_test(invoice is not None, "Invoice automatically generated from won deal", f"Invoice #: {invoice.invoice_number if invoice else 'N/A'}")
    if invoice:
        assert_test(invoice.amount == Decimal("125000.00"), "Invoice amount matches deal value", f"${invoice.amount}")
        assert_test(invoice.status == "issued", "Invoice status set to 'issued'")
        assert_test(invoice.customer == customer, "Invoice linked to exact customer")

    txn = Transaction.objects.filter(company=company, description__contains=deal.title).first()
    assert_test(txn is not None, "Financial Transaction posted automatically", f"Type: {txn.transaction_type if txn else 'N/A'}")
    if txn:
        assert_test(txn.transaction_type == "earn", "Transaction marked as 'earn' credit")
        assert_test(txn.amount == Decimal("125000.00"), "Transaction amount matches deal value")

    gl_entries = JournalEntry.objects.filter(company=company, reference_type="invoice", reference_id=str(invoice.id))
    assert_test(gl_entries.count() == 2, "Double-Entry General Ledger records created", f"Count: {gl_entries.count()}")
    debit_entry = gl_entries.filter(entry_type="debit").first()
    credit_entry = gl_entries.filter(entry_type="credit").first()
    assert_test(debit_entry and debit_entry.account_code == "1200_ACCOUNTS_RECEIVABLE", "GL Debit: Accounts Receivable (1200)")
    assert_test(credit_entry and credit_entry.account_code == "4000_REVENUE", "GL Credit: Sales Revenue (4000)")

    # -------------------------------------------------------------
    # TEST 5: Projects BIOM - Delivery Project & Tasks
    # -------------------------------------------------------------
    print("\n--- Phase 5: Projects BIOM Auto-Provisioning ---")
    expected_project_name = f"Delivery: {deal.title}"
    project = Project.objects.filter(company=company, customer=customer, name=expected_project_name).first()
    assert_test(project is not None, "Delivery Project automatically provisioned", f"Name: {project.name if project else 'N/A'}")
    if project:
        assert_test(project.status == "planned", "Project status set to 'planned'")
        tasks = Task.objects.filter(project=project)
        assert_test(tasks.count() == 3, "Baseline implementation tasks provisioned", f"Tasks count: {tasks.count()}")
        task_titles = list(tasks.values_list('title', flat=True))
        assert_test("Kickoff & Requirements Gathering" in task_titles, "Task: Kickoff & Requirements Gathering present")
        assert_test("Implementation & Development" in task_titles, "Task: Implementation & Development present")
        assert_test("Testing & QA" in task_titles, "Task: Testing & QA present")

    # -------------------------------------------------------------
    # TEST 6: Service BIOM - Customer Onboarding & SLA Ticket
    # -------------------------------------------------------------
    print("\n--- Phase 6: Service BIOM Auto-Provisioning ---")
    expected_ticket_title = f"Customer Onboarding: {deal.title}"
    ticket = ServiceTicket.objects.filter(company=company, customer=customer, title=expected_ticket_title).first()
    assert_test(ticket is not None, "Customer Onboarding ServiceTicket opened", f"Ticket ID: {ticket.id if ticket else 'N/A'}")
    if ticket:
        assert_test(ticket.priority == "high", "Onboarding ticket assigned Priority 'high'")
        assert_test(ticket.status == "open", "Onboarding ticket status set to 'open'")

    # -------------------------------------------------------------
    # TEST 7: HRMS BIOM - Resource Allocation Request
    # -------------------------------------------------------------
    print("\n--- Phase 7: HRMS BIOM Resource Allocation Activity ---")
    expected_act_title = f"Resource Allocation Required: {deal.title}"
    activity = Activity.objects.filter(company=company, deal=deal, activity_type="system", title=expected_act_title).first()
    assert_test(activity is not None, "HRMS Resource Allocation system activity logged", f"Title: {activity.title if activity else 'N/A'}")

    # -------------------------------------------------------------
    # TEST 8: Orchestration Idempotency Verification
    # -------------------------------------------------------------
    print("\n--- Phase 8: Idempotency & Duplicate Prevention ---")
    second_orch = orchestrate_deal_won(deal.id)
    assert_test(second_orch is not None, "Re-running orchestration handles idempotent calls gracefully")
    # Verify no duplicate invoices or projects created
    all_invoices = Invoice.objects.filter(deal=deal).count()
    all_projects = Project.objects.filter(company=company, customer=customer, name=expected_project_name).count()
    all_tickets = ServiceTicket.objects.filter(company=company, customer=customer, title=expected_ticket_title).count()
    assert_test(all_invoices == 1, "Idempotency: Exactly 1 invoice exists for deal (no duplicates)")
    assert_test(all_projects == 1, "Idempotency: Exactly 1 delivery project exists for deal (no duplicates)")
    assert_test(all_tickets == 1, "Idempotency: Exactly 1 onboarding ticket exists for deal (no duplicates)")

    # -------------------------------------------------------------
    # TEST 9: Orchestration Status API Endpoint
    # -------------------------------------------------------------
    print("\n--- Phase 9: DRF Orchestration Status API View ---")
    factory = APIRequestFactory()
    view = OrchestrationStatusView.as_view()

    # GET request with deal_id
    req_get = factory.get(f'/api/crm/orchestration/?deal_id={deal.id}')
    force_authenticate(req_get, user=admin_user)
    resp_get = view(req_get)
    assert_test(resp_get.status_code == 200, "API GET /api/crm/orchestration/?deal_id= returns 200 OK")
    api_data = resp_get.data
    assert_test(api_data.get("orchestrated") is True, "API response confirms orchestrated = True")
    assert_test(len(api_data.get("finance", {}).get("invoices", [])) >= 1, "API response contains generated invoice")
    assert_test(len(api_data.get("projects", [])) >= 1, "API response contains delivery project")
    assert_test(len(api_data.get("service", {}).get("tickets", [])) >= 1, "API response contains onboarding ticket")
    assert_test(len(api_data.get("hrms", {}).get("activities", [])) >= 1, "API response contains HRMS activities")

    print("\n" + "=" * 70)
    print(f"TEST RESULTS: {passed} PASSED, {failed} FAILED")
    print("=" * 70)
    return failed == 0

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
