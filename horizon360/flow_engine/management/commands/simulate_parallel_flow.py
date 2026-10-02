from django.core.management.base import BaseCommand
from django.conf import settings
from flow_engine.models import FlowDefinition, FlowVersion, FlowNode, FlowEdge, Company, StepExecution
from flow_engine.runtime import FlowRuntime
import uuid

class Command(BaseCommand):
    help = 'Runs a simulation of Parallel Forks & Joins'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("--- Horizon Parallel Flow Simulation ---"))
        
        # 1. Force Celery to run synchronously for this simulation
        settings.CELERY_TASK_ALWAYS_EAGER = True
        
        company = Company.objects.first()
        if not company:
            company = Company.objects.create(name="Simulated Corp")

        # 2. Create a fresh Test Flow
        flow = FlowDefinition.objects.create(
            name="E2E Parallel Fan-Out Flow",
            description="Simulated flow testing AND-Joins",
            company=company,
            trigger_type="event",
            trigger_event="employee.onboarded",
            is_active=True
        )
        
        version = FlowVersion.objects.create(
            flow=flow,
            version_number=1,
            status="published"
        )
        
        # 3. Create Nodes
        trigger_id = str(uuid.uuid4())
        it_setup_id = str(uuid.uuid4())
        hr_setup_id = str(uuid.uuid4())
        facility_setup_id = str(uuid.uuid4())
        join_id = str(uuid.uuid4())
        end_id = str(uuid.uuid4())
        
        FlowNode.objects.create(version=version, canvas_node_id=trigger_id, node_type="trigger", label="Onboard Trigger", position_x=100, position_y=200)
        
        # Parallel Branch 1
        FlowNode.objects.create(version=version, canvas_node_id=it_setup_id, node_type="action", label="IT Provisioning", position_x=300, position_y=100, config={"action_type": "setup_it"})
        # Parallel Branch 2
        FlowNode.objects.create(version=version, canvas_node_id=hr_setup_id, node_type="action", label="HR Payroll Setup", position_x=300, position_y=200, config={"action_type": "setup_hr"})
        # Parallel Branch 3
        FlowNode.objects.create(version=version, canvas_node_id=facility_setup_id, node_type="action", label="Badge Creation", position_x=300, position_y=300, config={"action_type": "setup_facility"})
        
        # Join Node
        FlowNode.objects.create(version=version, canvas_node_id=join_id, node_type="parallel_join", label="Wait for All", position_x=500, position_y=200)
        
        # End Node
        FlowNode.objects.create(version=version, canvas_node_id=end_id, node_type="end", label="End", position_x=700, position_y=200)
        
        # 4. Create Edges
        # Fork
        FlowEdge.objects.create(version=version, edge_id=str(uuid.uuid4()), source_node=trigger_id, target_node=it_setup_id)
        FlowEdge.objects.create(version=version, edge_id=str(uuid.uuid4()), source_node=trigger_id, target_node=hr_setup_id)
        FlowEdge.objects.create(version=version, edge_id=str(uuid.uuid4()), source_node=trigger_id, target_node=facility_setup_id)
        
        # Join
        FlowEdge.objects.create(version=version, edge_id=str(uuid.uuid4()), source_node=it_setup_id, target_node=join_id)
        FlowEdge.objects.create(version=version, edge_id=str(uuid.uuid4()), source_node=hr_setup_id, target_node=join_id)
        FlowEdge.objects.create(version=version, edge_id=str(uuid.uuid4()), source_node=facility_setup_id, target_node=join_id)
        
        # Out
        FlowEdge.objects.create(version=version, edge_id=str(uuid.uuid4()), source_node=join_id, target_node=end_id)
        
        self.stdout.write("Created test parallel flow definition.")
        
        # 5. Execute Flow!
        self.stdout.write(self.style.WARNING("Starting DAG Execution (Synchronous Mode)..."))
        
        runtime = FlowRuntime()
        
        execution = runtime.start_execution(flow.id, {"employee_name": "Alice"})
        
        # Note: start_execution automatically fires the trigger which recursively fires execute_node_task.
        # Since CELERY_TASK_ALWAYS_EAGER=True, it will run the entire graph synchronously here!
        
        execution.refresh_from_db()
        
        self.stdout.write(self.style.SUCCESS(f"\nExecution Complete! Final Status: {execution.status}"))
        self.stdout.write(f"Execution ID: {execution.id}")
        
        # Validate Steps
        completed_steps = StepExecution.objects.filter(execution=execution).order_by('started_at')
        for step in completed_steps:
            self.stdout.write(f" - [{step.status.upper()}] Node: {step.node.label} (ID: {step.canvas_node_id})")
        
        # Print URLs
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("SIMULATION SUCCESSFUL"))
        self.stdout.write("="*50)
        self.stdout.write("View the trace in the Visual Debugger:")
        self.stdout.write(self.style.WARNING(f"http://localhost:5173/executions/{execution.id}"))
        self.stdout.write("="*50)
