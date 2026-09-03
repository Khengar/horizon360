from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from cdp_core.models import Company, Customer, UserProfile, Workflow, RawEvent
from marketing.models import Campaign, Lead
from crm.models import Deal
from finance.models import Invoice, Expense, Product
from projects.models import Project
from service.models import ServiceTicket
from hrms.models import Department, Employee
from partner.models import Partner, PartnerOpportunity
from vendor.models import Vendor, PurchaseOrder
from integrations.models import Integration
from cdp_core.workflow_service import execute_workflows

class Command(BaseCommand):
    help = 'Seeds realistic demo data for Horizon 360.'

    def handle(self, *args, **options):
        self.stdout.write("Starting Demo Data Seeding...")
        
        # 1. Identity & Tenant Setup (Idempotent)
        company, created = Company.objects.get_or_create(name="Quantumard Global")
        user, _ = User.objects.get_or_create(username="demo_admin", defaults={"email": "admin@quantumard.com"})
        user.set_password("demo123")
        user.save()
        UserProfile.objects.get_or_create(user=user, defaults={"company": company})

        # Customer setup
        cust1, _ = Customer.objects.get_or_create(company=company, primary_email="acme@corp.com", defaults={"primary_phone": "555-0100", "attributes": {"name": "Acme Corp"}})
        cust2, _ = Customer.objects.get_or_create(company=company, primary_email="tech@solutions.net", defaults={"primary_phone": "555-0200", "attributes": {"name": "Tech Solutions"}})

        # Integrations Setup
        stripe, _ = Integration.objects.get_or_create(company=company, provider='stripe_demo', defaults={'name': 'Stripe Demo', 'direction': 'bi_directional', 'config': {'webhook_secret': 'demo-secret-123'}})
        hubspot, _ = Integration.objects.get_or_create(company=company, provider='hubspot_demo', defaults={'name': 'HubSpot Demo', 'direction': 'bi_directional', 'config': {'webhook_secret': 'demo-secret-123'}})

        # Workflows
        workflows = [
            {"name": "Deal Won -> Create Invoice", "trigger_event": "deal.won", "action_type": "create_invoice", "source_biom": "Sales", "destination_biom": "Finance"},
            {"name": "Invoice Paid -> Create Project", "trigger_event": "invoice.paid", "action_type": "create_project", "source_biom": "Finance", "destination_biom": "Projects"},
            {"name": "Project Created -> Create Ticket", "trigger_event": "project.created", "action_type": "create_ticket", "source_biom": "Projects", "destination_biom": "Service"},
            {"name": "Deal Won -> Sync HubSpot", "trigger_event": "deal.won", "action_type": "send_integration_event", "source_biom": "Sales", "destination_biom": "External", "action_event_name": "hubspot_demo"},
        ]
        
        for w in workflows:
            action_event_name = w.get("action_event_name", "")
            Workflow.objects.get_or_create(
                company=company, name=w["name"], 
                defaults={"trigger_event": w["trigger_event"], "action_type": w["action_type"], "source_biom": w["source_biom"], "destination_biom": w["destination_biom"], "action_event_name": action_event_name, "is_active": True}
            )

        # 2. Marketing BIOM
        campaign, _ = Campaign.objects.get_or_create(company=company, name="Q4 Global Expansion", defaults={"status": "active", "budget": "50000.00"})
        lead, _ = Lead.objects.get_or_create(company=company, email="acme@corp.com", defaults={"campaign": campaign, "name": "Acme Rep", "status": "converted"})
        
        # 3. Sales BIOM
        deal, _ = Deal.objects.get_or_create(company=company, customer=cust1, title="Enterprise Subscription - Acme", defaults={"value": 120000.00, "stage": "won"})

        # 4. Finance BIOM
        Expense.objects.get_or_create(company=company, description="Server Hosting Q4", defaults={"amount": 4500.00, "status": "paid"})
        Expense.objects.get_or_create(company=company, description="Marketing Agency Retainer", defaults={"amount": 12500.00, "status": "pending"})
        
        # Generate the deal.won event to trigger the chain
        if created or not RawEvent.objects.filter(company=company, event_name="deal.won").exists():
            event_won = RawEvent.objects.create(
                company=company, customer=cust1, event_name="deal.won",
                raw_payload={"id": deal.id, "value": float(deal.value)}, processed=False
            )
            execute_workflows(event_won)
            
            # The workflow creates an invoice, let's find it and pay it
            invoice = Invoice.objects.filter(company=company, deal=deal).first()
            if invoice:
                invoice.status = 'paid'
                invoice.save()
                event_paid = RawEvent.objects.create(
                    company=company, customer=cust1, event_name="invoice.paid",
                    raw_payload={"invoice_id": invoice.id, "amount": float(invoice.amount)}, processed=False
                )
                execute_workflows(event_paid)
                
                # The workflow creates a project, let's trigger project.created
                project = Project.objects.filter(company=company, customer=cust1).first()
                if project:
                    event_proj = RawEvent.objects.create(
                        company=company, customer=cust1, event_name="project.created",
                        raw_payload={"project_id": project.id}, processed=False
                    )
                    execute_workflows(event_proj)

        # 7. HRMS BIOM
        dept, _ = Department.objects.get_or_create(company=company, name="Engineering")
        emp, _ = Employee.objects.get_or_create(company=company, email="alice.smith@quantumard.com", defaults={"department": dept, "first_name": "Alice", "last_name": "Smith", "role": "Senior Engineer", "status": "active"})
        
        # Add Product to Finance BIOM
        prod, _ = Product.objects.get_or_create(company=company, sku="SRV-001", defaults={"name": "Cloud Storage 1TB", "price": 150.00})
        
        # 9. Partner BIOM
        partner, _ = Partner.objects.get_or_create(company=company, email="alliance@sys.com", defaults={"name": "Alliance Systems", "type": "Reseller", "status": "active"})
        popp, _ = PartnerOpportunity.objects.get_or_create(company=company, partner=partner, name="Alliance EMEA Deal", defaults={"value": 45000.00, "stage": "open"})
        
        # 10. Vendor BIOM
        vendor, _ = Vendor.objects.get_or_create(company=company, email="supplies@office.com", defaults={"name": "Office Suppliers Inc", "category": "Equipment", "status": "active"})
        po, _ = PurchaseOrder.objects.get_or_create(company=company, vendor=vendor, reference="PO-2026-991", defaults={"amount": 4500.00, "status": "approved"})

        self.stdout.write(self.style.SUCCESS('Successfully seeded Horizon 360 demo data!'))
