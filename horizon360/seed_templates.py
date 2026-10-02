import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horizon360.settings')
django.setup()

from flow_engine.models import FlowMarketplaceTemplate

templates = [
    {
        "name": "Employee Onboarding (Standard)",
        "description": "Orchestrates IT provisioning, HR compliance, and initial training assignment across multiple BIOMs.",
        "category": "HR",
        "source_bioms": ["HR"],
        "target_bioms": ["IT", "Finance"],
        "tags": ["Onboarding", "Compliance"],
        "icon": "users",
        "template_data": {
            "trigger": "hr.employee.created",
            "nodes": [
                {"id": "trigger_1", "type": "trigger", "label": "New Hire Created", "config": {"trigger_event": "hr.employee.created"}},
                {"id": "action_it", "type": "action", "label": "Provision Email", "config": {"action_type": "create_account"}},
                {"id": "approval_mgr", "type": "approval", "label": "Manager Access Approval", "config": {"title": "Approve software access"}},
                {"id": "end_1", "type": "end", "label": "End Flow"}
            ],
            "edges": [
                {"id": "e1", "source_node": "trigger_1", "target_node": "action_it"},
                {"id": "e2", "source_node": "action_it", "target_node": "approval_mgr"},
                {"id": "e3", "source_node": "approval_mgr", "target_node": "end_1"}
            ]
        }
    },
    {
        "name": "Automated Invoice Chaser",
        "description": "Automatically follows up on overdue invoices via email and escalates to Account Manager if >30 days late.",
        "category": "Finance",
        "source_bioms": ["Finance"],
        "target_bioms": ["Sales"],
        "tags": ["Collections", "Billing"],
        "icon": "dollar-sign",
        "template_data": {
            "trigger": "finance.invoice.overdue",
            "nodes": []
        }
    },
    {
        "name": "Deal Won Orchestration",
        "description": "Moves a won opportunity into a live project, triggers billing, and assigns customer success.",
        "category": "Sales",
        "source_bioms": ["Sales"],
        "target_bioms": ["Projects", "Finance", "Service"],
        "tags": ["CRM", "Handoff"],
        "icon": "briefcase",
        "template_data": {
            "trigger": "crm.deal.won",
            "nodes": []
        }
    },
    {
        "name": "Security Incident Response",
        "description": "Rapidly triggers system lockdowns, notifies SecOps, and files compliance reports upon breach detection.",
        "category": "IT",
        "source_bioms": ["IT"],
        "target_bioms": ["Legal", "Exec"],
        "tags": ["Security", "SLA"],
        "icon": "shield",
        "template_data": {
            "trigger": "it.security.alert",
            "nodes": []
        }
    },
    {
        "name": "Purchase Order Approval (Multi-Tier)",
        "description": "Routes POs through Finance and Exec based on total amount.",
        "category": "Finance",
        "source_bioms": ["Procurement"],
        "target_bioms": ["Finance", "Exec"],
        "tags": ["Approvals", "Spend"],
        "icon": "check-circle",
        "template_data": {
            "trigger": "procurement.po.submitted",
            "nodes": []
        }
    },
    {
        "name": "Customer Churn Risk Alert",
        "description": "Uses AI to detect negative sentiment in support tickets and warns Account Managers.",
        "category": "Service",
        "source_bioms": ["Service"],
        "target_bioms": ["Sales", "AI"],
        "tags": ["Retention", "AI"],
        "icon": "alert-triangle",
        "template_data": {
            "trigger": "service.ticket.updated",
            "nodes": []
        }
    },
    {
        "name": "Marketing Campaign Lead Sync",
        "description": "Syncs webinar attendees to Sales Pipeline as MQLs.",
        "category": "Marketing",
        "source_bioms": ["Marketing"],
        "target_bioms": ["Sales"],
        "tags": ["Lead Gen", "Sync"],
        "icon": "users",
        "template_data": {
            "trigger": "marketing.campaign.ended",
            "nodes": []
        }
    },
    {
        "name": "Vendor SLA Breach Escalation",
        "description": "Escalates support tickets when third-party vendors fail to meet their contracted SLAs.",
        "category": "Vendor",
        "source_bioms": ["Vendor"],
        "target_bioms": ["Service", "Legal"],
        "tags": ["SLA", "Compliance"],
        "icon": "clock",
        "template_data": {
            "trigger": "vendor.sla.breach",
            "nodes": []
        }
    },
    {
        "name": "Employee Offboarding",
        "description": "Revokes access, processes final payroll, and schedules exit interview.",
        "category": "HR",
        "source_bioms": ["HR"],
        "target_bioms": ["IT", "Finance"],
        "tags": ["Offboarding", "Security"],
        "icon": "log-out",
        "template_data": {
            "trigger": "hr.employee.terminated",
            "nodes": []
        }
    },
    {
        "name": "Partner Deal Registration",
        "description": "Validates channel partner deal registrations and alerts direct sales for conflict checks.",
        "category": "Partner",
        "source_bioms": ["Partner"],
        "target_bioms": ["Sales"],
        "tags": ["Channel", "CRM"],
        "icon": "share-2",
        "template_data": {
            "trigger": "partner.deal.registered",
            "nodes": []
        }
    },
    {
        "name": "Weekly Data Backup Audit",
        "description": "Runs a cron schedule every Friday to verify database backups and notify DevOps.",
        "category": "IT",
        "source_bioms": ["IT"],
        "target_bioms": ["DevOps"],
        "tags": ["Cron", "Maintenance"],
        "icon": "database",
        "template_data": {
            "trigger": "0 0 * * 5",
            "nodes": []
        }
    },
    {
        "name": "Contract Renewal Reminder",
        "description": "Notifies Sales 90, 60, and 30 days before customer contract expires.",
        "category": "Sales",
        "source_bioms": ["Finance"],
        "target_bioms": ["Sales"],
        "tags": ["Renewals", "Timer"],
        "icon": "calendar",
        "template_data": {
            "trigger": "finance.contract.active",
            "nodes": []
        }
    },
    {
        "name": "Expense Report Reimbursement",
        "description": "Approves employee expenses and schedules them in the next payout run.",
        "category": "Finance",
        "source_bioms": ["HR"],
        "target_bioms": ["Finance"],
        "tags": ["Payroll", "Approvals"],
        "icon": "credit-card",
        "template_data": {
            "trigger": "hr.expense.submitted",
            "nodes": []
        }
    },
    {
        "name": "Bug Report Triage (AI)",
        "description": "Uses LLM to categorize inbound bug reports and route to the correct engineering squad.",
        "category": "Projects",
        "source_bioms": ["Service"],
        "target_bioms": ["Projects", "AI"],
        "tags": ["DevOps", "AI"],
        "icon": "bug",
        "template_data": {
            "trigger": "service.ticket.bug",
            "nodes": []
        }
    },
    {
        "name": "Social Media Auto-Publisher",
        "description": "Takes approved content blocks and publishes them to LinkedIn and Twitter at scheduled times.",
        "category": "Marketing",
        "source_bioms": ["Marketing"],
        "target_bioms": ["Social"],
        "tags": ["Content", "Cron"],
        "icon": "share-2",
        "template_data": {
            "trigger": "marketing.post.approved",
            "nodes": []
        }
    },
    {
        "name": "Inventory Low Stock Alert",
        "description": "Triggers purchase orders when warehouse inventory drops below defined thresholds.",
        "category": "Operations",
        "source_bioms": ["Operations"],
        "target_bioms": ["Procurement"],
        "tags": ["Supply Chain", "ERP"],
        "icon": "package",
        "template_data": {
            "trigger": "ops.inventory.low",
            "nodes": []
        }
    },
    {
        "name": "Lead Scoring & Enrichment",
        "description": "Enriches new leads with Clearbit data and assigns AI score before routing to SDRs.",
        "category": "Marketing",
        "source_bioms": ["Marketing"],
        "target_bioms": ["Sales", "AI"],
        "tags": ["Enrichment", "AI"],
        "icon": "zap",
        "template_data": {
            "trigger": "marketing.lead.created",
            "nodes": []
        }
    },
    {
        "name": "Candidate Interview Loop",
        "description": "Orchestrates multi-stage interview scheduling and collects feedback from hiring panel.",
        "category": "HR",
        "source_bioms": ["HR"],
        "target_bioms": ["Operations"],
        "tags": ["Recruiting", "Approvals"],
        "icon": "users",
        "template_data": {
            "trigger": "hr.candidate.advanced",
            "nodes": []
        }
    },
    {
        "name": "Customer Feedback Survey",
        "description": "Sends NPS survey 7 days after issue resolution and creates escalation if score is <= 6.",
        "category": "Service",
        "source_bioms": ["Service"],
        "target_bioms": ["Marketing", "Sales"],
        "tags": ["NPS", "Feedback"],
        "icon": "smile",
        "template_data": {
            "trigger": "service.ticket.resolved",
            "nodes": []
        }
    },
    {
        "name": "Compliance GDPR Data Deletion",
        "description": "Executes Right to be Forgotten requests by purging data across all BIOM databases.",
        "category": "IT",
        "source_bioms": ["Legal"],
        "target_bioms": ["IT", "Marketing", "Sales"],
        "tags": ["Compliance", "GDPR"],
        "icon": "trash-2",
        "template_data": {
            "trigger": "legal.gdpr.deletion",
            "nodes": []
        }
    },
    {
        "name": "End of Month Financial Close",
        "description": "Automates the gathering of departmental P&L reports and enforces sign-off from all VPs.",
        "category": "Finance",
        "source_bioms": ["Finance"],
        "target_bioms": ["Exec", "All BIOMs"],
        "tags": ["Accounting", "Approvals"],
        "icon": "bar-chart-2",
        "template_data": {
            "trigger": "0 17 28 * *",
            "nodes": []
        }
    }
]

print("Clearing old templates...")
FlowMarketplaceTemplate.objects.all().delete()

print(f"Inserting {len(templates)} templates...")
for t in templates:
    FlowMarketplaceTemplate.objects.create(**t)
    
print("Successfully seeded marketplace templates.")
