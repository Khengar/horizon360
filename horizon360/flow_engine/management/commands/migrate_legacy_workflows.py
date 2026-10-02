import json
import uuid
from django.core.management.base import BaseCommand
from django.db import transaction
from cdp_core.models import Workflow as LegacyWorkflow
from crm.models import Company
from flow_engine.models import FlowDefinition, FlowVersion, FlowNode, FlowEdge

class Command(BaseCommand):
    help = 'Migrates legacy cdp_core.Workflow and hardcoded orchestrations into the new Flow Engine.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting legacy workflow migration...")

        with transaction.atomic():
            self._migrate_cdp_workflows()
            self._migrate_deal_won_orchestration()

        self.stdout.write(self.style.SUCCESS("Migration completed successfully."))

    def _migrate_cdp_workflows(self):
        legacy_workflows = LegacyWorkflow.objects.all()
        if not legacy_workflows.exists():
            self.stdout.write("No legacy CDP workflows found to migrate.")
            return

        migrated_count = 0
        for legacy in legacy_workflows:
            self.stdout.write(f"Migrating CDP Workflow: {legacy.name}")
            
            # Create Flow Definition
            flow_def = FlowDefinition.objects.create(
                company=legacy.company,
                name=f"[Migrated] {legacy.name}",
                description=f"Migrated from legacy CDP. Source BIOM: {legacy.source_biom}, Dest: {legacy.destination_biom}",
                category='cross_biom',
                trigger_type='webhook',
                is_active=legacy.is_active
            )

            # Create Draft Version
            version = FlowVersion.objects.create(
                flow=flow_def,
                version_number=1,
                status='published'
            )

            # Nodes list for React Flow Canvas
            canvas_nodes = []
            canvas_edges = []

            # 1. Trigger Node
            trigger_id = str(uuid.uuid4())
            FlowNode.objects.create(
                version=version,
                canvas_node_id=trigger_id,
                node_type='trigger',
                label='Event Trigger',
                position_x=250,
                position_y=50,
                config={
                    'event_topic': legacy.trigger_event,
                    'is_legacy_migrated': True
                }
            )
            canvas_nodes.append({
                "id": trigger_id,
                "type": "trigger",
                "position": {"x": 250, "y": 50},
                "data": {"type": "trigger", "label": "Event Trigger"}
            })

            last_node_id = trigger_id
            y_pos = 150

            # 2. Condition Node (if exists)
            if legacy.condition_field:
                cond_id = str(uuid.uuid4())
                FlowNode.objects.create(
                    version=version,
                    canvas_node_id=cond_id,
                    node_type='condition',
                    label='Legacy Condition',
                    position_x=250,
                    position_y=y_pos,
                    config={
                        'field': legacy.condition_field,
                        'operator': legacy.condition_operator,
                        'value': legacy.condition_value
                    }
                )
                
                # Edge: Trigger -> Condition
                edge_id = f"e-{trigger_id}-{cond_id}"
                FlowEdge.objects.create(
                    version=version,
                    edge_id=edge_id,
                    source_node=trigger_id,
                    target_node=cond_id,
                    source_handle='default'
                )

                canvas_nodes.append({
                    "id": cond_id,
                    "type": "condition",
                    "position": {"x": 250, "y": y_pos},
                    "data": {"type": "condition", "label": "Legacy Condition"}
                })
                canvas_edges.append({
                    "id": edge_id,
                    "source": trigger_id,
                    "target": cond_id
                })

                last_node_id = cond_id
                y_pos += 100

            # 3. Action Node
            action_id = str(uuid.uuid4())
            FlowNode.objects.create(
                version=version,
                canvas_node_id=action_id,
                node_type='action',
                label=legacy.action_type,
                position_x=250,
                position_y=y_pos,
                config={
                    'action_type': legacy.action_type,
                    'action_event_name': legacy.action_event_name,
                    'destination_biom': legacy.destination_biom
                }
            )
            
            # Edge: Condition (or Trigger) -> Action
            edge_id = f"e-{last_node_id}-{action_id}"
            source_handle = 'true' if legacy.condition_field else 'default'
            
            FlowEdge.objects.create(
                version=version,
                edge_id=edge_id,
                source_node=last_node_id,
                target_node=action_id,
                source_handle=source_handle
            )

            canvas_nodes.append({
                "id": action_id,
                "type": "action",
                "position": {"x": 250, "y": y_pos},
                "data": {"type": "action", "label": legacy.action_type}
            })
            canvas_edges.append({
                "id": edge_id,
                "source": last_node_id,
                "sourceHandle": source_handle,
                "target": action_id
            })

            # Save canvas layout
            version.canvas_data = {
                "nodes": canvas_nodes,
                "edges": canvas_edges
            }
            version.save()
            migrated_count += 1
            
        self.stdout.write(f"Migrated {migrated_count} CDP workflows.")

    def _migrate_deal_won_orchestration(self):
        # Create a Global Deal Won Orchestration for the first Company (or all companies)
        # For simplicity, we'll create it for the first company in the system, or skip if none.
        company = Company.objects.first()
        if not company:
            self.stdout.write("No companies found. Skipping Deal Won Orchestration migration.")
            return
            
        flow_name = "System: Deal Won Orchestration"
        if FlowDefinition.objects.filter(name=flow_name).exists():
            self.stdout.write("Deal Won Orchestration already exists.")
            return
            
        self.stdout.write(f"Migrating hardcoded Deal Won Orchestration for company {company.name}")
        
        flow_def = FlowDefinition.objects.create(
            company=company,
            name=flow_name,
            description="Automated orchestration previously hardcoded in crm/orchestration.py",
            category='cross_biom',
            trigger_type='webhook',
            is_active=True
        )

        version = FlowVersion.objects.create(
            flow=flow_def,
            version_number=1,
            status='published'
        )

        nodes = []
        edges = []
        db_edges = []
        
        # Helper to generate nodes
        def add_node(n_type, label, config, y_pos):
            nid = str(uuid.uuid4())
            FlowNode.objects.create(
                version=version,
                canvas_node_id=nid,
                node_type=n_type,
                label=label,
                position_x=250,
                position_y=y_pos,
                config=config
            )
            nodes.append({
                "id": nid,
                "type": n_type,
                "position": {"x": 250, "y": y_pos},
                "data": {"type": n_type, "label": label, "config": config}
            })
            return nid
            
        def add_edge(src, tgt):
            eid = f"e-{src}-{tgt}"
            FlowEdge.objects.create(
                version=version,
                edge_id=eid,
                source_node=src,
                target_node=tgt,
                source_handle='default'
            )
            edges.append({
                "id": eid,
                "source": src,
                "target": tgt
            })

        # 1. Trigger
        t_id = add_node('trigger', 'Deal Won Trigger', {'event_topic': 'crm.deal.won'}, 50)
        
        # 2. Parallel Fork
        f_id = add_node('parallel_fork', 'Fork', {}, 150)
        add_edge(t_id, f_id)
        
        # 3. Actions (Run in parallel)
        a1_id = add_node('action', 'Create Invoice & GL', {'action_type': 'create_invoice', 'destination_biom': 'finance'}, 250)
        a2_id = add_node('action', 'Create Delivery Project', {'action_type': 'create_project', 'destination_biom': 'projects'}, 250)
        a3_id = add_node('action', 'Create Onboarding Ticket', {'action_type': 'create_ticket', 'destination_biom': 'service'}, 250)
        a4_id = add_node('action', 'Request Resourcing', {'action_type': 'create_activity', 'destination_biom': 'hrms'}, 250)
        
        # Link fork to actions
        for action_id in [a1_id, a2_id, a3_id, a4_id]:
            add_edge(f_id, action_id)
            
        # 4. Parallel Join
        j_id = add_node('parallel_join', 'Join', {}, 350)
        for action_id in [a1_id, a2_id, a3_id, a4_id]:
            add_edge(action_id, j_id)
            
        # 5. End
        e_id = add_node('end', 'End', {}, 450)
        add_edge(j_id, e_id)
        
        version.canvas_data = {
            "nodes": nodes,
            "edges": edges
        }
        version.save()
        
        self.stdout.write("Successfully migrated hardcoded orchestration to Flow Engine.")
