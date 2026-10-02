from django.core.management.base import BaseCommand
from django.conf import settings
from flow_engine.models import FlowDefinition, FlowVersion, FlowNode, FlowEdge, Company
from flow_engine.runtime import FlowRuntime
from django.contrib.auth.models import User
import uuid

class Command(BaseCommand):
    help = 'Runs an end-to-end simulation of the Horizon Flow Engine'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("--- Horizon Flow Engine E2E Simulation ---"))
        
        # 1. Force Celery to run synchronously for this simulation
        settings.CELERY_TASK_ALWAYS_EAGER = True
        
        company = Company.objects.first()
        if not company:
            company = Company.objects.create(name="Simulated Corp")
            
        # Ensure a superuser exists for approvals
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin')

        # 2. Create a fresh Test Flow
        flow = FlowDefinition.objects.create(
            name="E2E Billing Approval Flow",
            description="Simulated flow for E2E debugger testing",
            company=company,
            trigger_type="event",
            trigger_event="order.completed",
            is_active=True
        )
        
        version = FlowVersion.objects.create(
            flow=flow,
            version_number=1,
            status="published"
        )
        
        # 3. Create Nodes
        trigger_id = str(uuid.uuid4())
        action_id = str(uuid.uuid4())
        approval_id = str(uuid.uuid4())
        end_id = str(uuid.uuid4())
        
        FlowNode.objects.create(
            version=version, canvas_node_id=trigger_id, node_type="trigger",
            label="Order Completed", position_x=100, position_y=100,
            config={}
        )
        FlowNode.objects.create(
            version=version, canvas_node_id=action_id, node_type="action",
            label="Generate Invoice", position_x=300, position_y=100,
            config={"action_type": "create_invoice", "params": {"amount": "{{trigger.payload.total_amount}}"}}
        )
        FlowNode.objects.create(
            version=version, canvas_node_id=approval_id, node_type="approval",
            label="Manager Approval", position_x=500, position_y=100,
            config={"title": "Approve Invoice for {{trigger.payload.customer_name}}", "description": "Please verify this high-value order."}
        )
        FlowNode.objects.create(
            version=version, canvas_node_id=end_id, node_type="end",
            label="End", position_x=700, position_y=100,
            config={}
        )
        
        # 4. Create Edges
        FlowEdge.objects.create(version=version, edge_id=str(uuid.uuid4()), source_node=trigger_id, target_node=action_id)
        FlowEdge.objects.create(version=version, edge_id=str(uuid.uuid4()), source_node=action_id, target_node=approval_id)
        FlowEdge.objects.create(version=version, edge_id=str(uuid.uuid4()), source_node=approval_id, target_node=end_id)
        
        self.stdout.write("Created test flow definition.")
        
        # 5. Execute Flow!
        self.stdout.write(self.style.WARNING("Starting DAG Execution (Synchronous Mode)..."))
        
        runtime = FlowRuntime()
        trigger_payload = {
            "event_id": str(uuid.uuid4()),
            "customer_name": "Acme Corp",
            "total_amount": 25000.00
        }
        
        execution = runtime.start_execution(flow.id, trigger_payload)
        
        # Manually advance the DAG for the simulation
        try:
            self.stdout.write("Running Trigger Node...")
            runtime.execute_node(str(execution.id), trigger_id)
            
            self.stdout.write("Running Action Node...")
            runtime.execute_node(str(execution.id), action_id)
            
            self.stdout.write("Running Approval Node...")
            runtime.execute_node(str(execution.id), approval_id)
            
            execution.refresh_from_db()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during execution: {e}"))
            
        self.stdout.write(self.style.SUCCESS(f"\nExecution Complete! Current Status: {execution.status}"))
        self.stdout.write(f"Execution ID: {execution.id}")
        
        # Print URLs
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("SIMULATION SUCCESSFUL"))
        self.stdout.write("="*50)
        self.stdout.write("View the trace in the Visual Debugger:")
        self.stdout.write(self.style.WARNING(f"http://localhost:5173/executions/{execution.id}"))
        self.stdout.write("\nView the pending task in the Approvals Inbox:")
        self.stdout.write(self.style.WARNING("http://localhost:5173/approvals"))
        self.stdout.write("="*50)
