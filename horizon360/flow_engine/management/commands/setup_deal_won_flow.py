from django.core.management.base import BaseCommand
from cdp_core.models import Company
from flow_engine.models import FlowDefinition, FlowVersion, FlowNode, FlowEdge

class Command(BaseCommand):
    help = 'Migrates the old Deal Won orchestration into a native Flow Engine definition.'

    def handle(self, *args, **options):
        company = Company.objects.first()
        if not company:
            self.stdout.write(self.style.ERROR('No Company found. Please run seed_data first.'))
            return
            
        # 1. Create Definition
        flow, created = FlowDefinition.objects.get_or_create(
            company=company,
            name='Deal Won Orchestration',
            defaults={
                'description': 'Automated cross-BIOM orchestration triggered when a deal is closed won.',
                'category': 'cross_biom',
                'is_active': True,
                'trigger_type': 'event',
                'trigger_event': 'deal.won',
                'icon': 'briefcase',
                'color': '#22c55e', # Green
            }
        )
        
        if not created:
            self.stdout.write(self.style.WARNING('Deal Won Flow already exists. Overwriting version...'))
            flow.versions.all().delete()
            
        # 2. Create Version
        version = FlowVersion.objects.create(
            flow=flow,
            version_number=1,
            status='published'
        )
        
        # 3. Create Nodes
        trigger = FlowNode.objects.create(
            version=version,
            node_id='trigger_1',
            node_type='trigger',
            label='Deal Won Event',
            position_x=100,
            position_y=100,
            config={'event_name': 'deal.won'}
        )
        
        invoice = FlowNode.objects.create(
            version=version,
            node_id='action_invoice',
            node_type='action',
            label='Create Initial Invoice',
            position_x=100,
            position_y=250,
            config={
                'action_type': 'create_invoice',
                'params': {
                    'deal_id': '{{trigger.payload.deal_id}}',
                    'amount': '{{trigger.payload.value}}',
                    'title': 'Invoice for {{trigger.payload.title}}'
                }
            }
        )
        
        project = FlowNode.objects.create(
            version=version,
            node_id='action_project',
            node_type='action',
            label='Provision Project',
            position_x=100,
            position_y=400,
            config={
                'action_type': 'create_project',
                'params': {
                    'deal_id': '{{trigger.payload.deal_id}}',
                    'name': 'Implementation: {{trigger.payload.title}}'
                }
            }
        )
        
        ticket = FlowNode.objects.create(
            version=version,
            node_id='action_ticket',
            node_type='action',
            label='Create Onboarding Ticket',
            position_x=100,
            position_y=550,
            config={
                'action_type': 'create_ticket',
                'params': {
                    'title': 'Onboarding - {{trigger.payload.title}}',
                    'priority': 'high'
                }
            }
        )
        
        end = FlowNode.objects.create(
            version=version,
            node_id='end_1',
            node_type='end',
            label='End Orchestration',
            position_x=100,
            position_y=700
        )
        
        # 4. Create Edges
        edges_data = [
            ('edge_1', 'trigger_1', 'action_invoice'),
            ('edge_2', 'action_invoice', 'action_project'),
            ('edge_3', 'action_project', 'action_ticket'),
            ('edge_4', 'action_ticket', 'end_1'),
        ]
        
        for e_id, source, target in edges_data:
            FlowEdge.objects.create(
                version=version,
                edge_id=e_id,
                source_node=source,
                target_node=target
            )
            
        # Update canvas state (mock for UI)
        version.canvas_data = {
            'nodes_layout': [
                {'id': 'trigger_1', 'position': {'x': 100, 'y': 100}},
                {'id': 'action_invoice', 'position': {'x': 100, 'y': 250}},
                {'id': 'action_project', 'position': {'x': 100, 'y': 400}},
                {'id': 'action_ticket', 'position': {'x': 100, 'y': 550}},
                {'id': 'end_1', 'position': {'x': 100, 'y': 700}},
            ]
        }
        version.save()
        
        self.stdout.write(self.style.SUCCESS('Successfully migrated Deal Won Orchestration to Flow Engine!'))
