from django.core.management.base import BaseCommand
from flow_engine.models import FlowMarketplaceTemplate
import json

class Command(BaseCommand):
    help = 'Seeds the database with standard Horizon Flow Engine Marketplace templates.'

    def handle(self, *args, **options):
        self.stdout.write('Seeding Flow Marketplace Templates...')
        
        templates = [
            {
                'name': 'Deal Won -> Project & Invoice (Standard)',
                'description': 'Automatically provisions an implementation project and generates the initial invoice when a deal is closed won.',
                'category': 'Sales to Delivery',
                'source_bioms': ['Sales'],
                'target_bioms': ['Projects', 'Finance'],
                'tags': ['sales', 'projects', 'finance', 'orchestration'],
                'icon': 'briefcase',
                'install_count': 1245,
                'rating': 4.8,
                'template_data': {
                    'trigger': 'deal.won',
                    'nodes': [
                        {'id': 'invoice', 'type': 'action', 'config': {'action_type': 'create_invoice'}},
                        {'id': 'project', 'type': 'action', 'config': {'action_type': 'create_project'}}
                    ]
                }
            },
            {
                'name': 'High-Value Invoice Approval',
                'description': 'Routes invoices over $10k through the CFO approval queue before sending to the client.',
                'category': 'Finance Governance',
                'source_bioms': ['Finance'],
                'target_bioms': ['Finance'],
                'tags': ['finance', 'approval', 'compliance'],
                'icon': 'shield',
                'install_count': 850,
                'rating': 4.9,
                'template_data': {
                    'trigger': 'invoice.created',
                    'condition': {'field': 'trigger.payload.amount', 'operator': '>=', 'value': '10000'},
                    'nodes': [
                        {'id': 'approval', 'type': 'approval', 'config': {'title': 'Approve High-Value Invoice'}}
                    ]
                }
            },
            {
                'name': 'Employee Onboarding Sequence',
                'description': 'Triggers IT asset provisioning, payroll setup, and schedules onboarding training when an employee accepts an offer.',
                'category': 'HR Operations',
                'source_bioms': ['HRMS'],
                'target_bioms': ['Vendor', 'Finance', 'Projects'],
                'tags': ['hrms', 'onboarding'],
                'icon': 'users',
                'install_count': 2100,
                'rating': 4.7,
                'template_data': {
                    'trigger': 'employee.hired',
                    'nodes': [
                        {'id': 'laptop', 'type': 'action', 'config': {'action_type': 'create_purchase_order'}},
                        {'id': 'payroll', 'type': 'action', 'config': {'action_type': 'setup_payroll'}}
                    ]
                }
            },
            {
                'name': 'Critical SLA Breach Escalation',
                'description': 'AI analyzes stalled tickets and pages the on-call manager if sentiment is negative.',
                'category': 'Service Recovery',
                'source_bioms': ['Service'],
                'target_bioms': ['HRMS', 'AI'],
                'tags': ['service', 'ai', 'escalation'],
                'icon': 'alert-triangle',
                'install_count': 530,
                'rating': 4.5,
                'template_data': {
                    'trigger': 'ticket.sla_breach',
                    'nodes': [
                        {'id': 'ai_sentiment', 'type': 'ai_action', 'config': {'prompt': 'Analyze ticket sentiment...'}}
                    ]
                }
            }
        ]
        
        for t in templates:
            FlowMarketplaceTemplate.objects.update_or_create(
                name=t['name'],
                defaults=t
            )
            
        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {len(templates)} marketplace templates!'))
