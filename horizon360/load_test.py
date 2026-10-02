import os
import django
import sys
import asyncio
import aiohttp
import time
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horizon360.settings')
django.setup()

from flow_engine.models import FlowDefinition, FlowVersion, FlowNode, FlowEdge

def setup_test_flow():
    # 1. Create dummy flow
    flow, created = FlowDefinition.objects.get_or_create(
        name="Load Test Flow (1000x)",
        defaults={
            "description": "Used for concurrent load testing",
            "trigger_type": "event",
            "trigger_event": "test.load"
        }
    )
    
    # 2. Create version
    version = FlowVersion.objects.create(
        flow=flow,
        version_number=1,
        is_active=True
    )
    
    # 3. Create nodes
    trigger = FlowNode.objects.create(flow_version=version, canvas_node_id="n1", node_type="trigger", label="Trigger", config={})
    action1 = FlowNode.objects.create(flow_version=version, canvas_node_id="n2", node_type="action", label="Simulated DB Work", config={"action_type": "dummy_work"})
    end = FlowNode.objects.create(flow_version=version, canvas_node_id="n3", node_type="end", label="End", config={})
    
    # 4. Create edges
    FlowEdge.objects.create(flow_version=version, edge_id="e1", source_node="n1", target_node="n2")
    FlowEdge.objects.create(flow_version=version, edge_id="e2", source_node="n2", target_node="n3")
    
    return flow.id

def get_auth_token():
    from django.contrib.auth import get_user_model
    from rest_framework_simplejwt.tokens import RefreshToken
    User = get_user_model()
    user = User.objects.first()
    if not user:
        user = User.objects.create_superuser('testadmin', 'admin@example.com', 'password')
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)

async def fire_execution(session, url, payload, headers, run_id):
    start = time.time()
    try:
        async with session.post(url, json=payload, headers=headers) as response:
            status = response.status
            data = await response.json()
            latency = time.time() - start
            return {"status": status, "id": data.get("execution_id"), "latency": latency, "run_id": run_id}
    except Exception as e:
        return {"status": 500, "error": str(e), "latency": time.time() - start, "run_id": run_id}

async def main():
    print("Setting up test flow...")
    flow_id = setup_test_flow()
    print(f"Flow Created: {flow_id}")
    
    print("Generating JWT Auth Token...")
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    url = f"http://127.0.0.1:8000/api/v2/flow-engine/flows/{flow_id}/execute/"
    payload = {"source": "load_test", "batch_size": 1000}
    
    CONCURRENT_REQUESTS = 1000
    
    print(f"Firing {CONCURRENT_REQUESTS} concurrent execution requests to {url}...")
    
    start_time = time.time()
    
    # Use aiohttp to fire requests concurrently
    async with aiohttp.ClientSession() as session:
        tasks = [fire_execution(session, url, payload, headers, i) for i in range(CONCURRENT_REQUESTS)]
        results = await asyncio.gather(*tasks)
        
    total_time = time.time() - start_time
    
    successes = [r for r in results if r["status"] == 202]
    failures = [r for r in results if r["status"] != 202]
    
    avg_latency = sum(r["latency"] for r in results) / len(results)
    
    print("\n--- Load Test Results ---")
    print(f"Total Requests: {CONCURRENT_REQUESTS}")
    print(f"Total Time: {total_time:.2f} seconds")
    print(f"Requests/sec: {CONCURRENT_REQUESTS / total_time:.2f}")
    print(f"Successful Queues: {len(successes)}")
    print(f"Failed Queues: {len(failures)}")
    print(f"Avg API Latency: {avg_latency*1000:.2f} ms")
    
    if failures:
        print(f"Sample Error: {failures[0]}")
        
    print("\nCheck celery worker logs to monitor processing throughput.")
    print("Run: celery -A horizon360 worker -l info")

if __name__ == "__main__":
    asyncio.run(main())
