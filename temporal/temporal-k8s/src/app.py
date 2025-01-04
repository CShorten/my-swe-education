import asyncio
import os
from datetime import timedelta
from aiohttp import web
from temporalio.client import Client
from prometheus_client import Counter, start_http_server
from typing import Optional

# Define Prometheus metrics
workflows_started = Counter('workflows_started_total', 'Number of workflows started')
workflow_failures = Counter('workflow_failures_total', 'Number of workflow start failures')

# Global client for reuse
_temporal_client: Optional[Client] = None

async def get_temporal_client() -> Client:
    """Create or return existing Temporal client with proper configuration."""
    global _temporal_client
    
    if not _temporal_client:
        _temporal_client = await Client.connect(
            os.getenv("TEMPORAL_HOST", "temporal.temporal.svc.cluster.local"),
            namespace=os.getenv("TEMPORAL_NAMESPACE", "default"),
            ssl=True,
            identity="python-orchestrator",
            tls_cert_path="/etc/temporal/certs/tls.crt",
            tls_key_path="/etc/temporal/certs/tls.key",
        )
    
    return _temporal_client

async def health_check(request: web.Request) -> web.Response:
    """Liveness probe endpoint for Kubernetes."""
    # Basic check - if we're running, we're alive
    return web.Response(text="healthy")

async def readiness_check(request: web.Request) -> web.Response:
    """Readiness probe endpoint for Kubernetes."""
    try:
        # Check if we can connect to Temporal
        client = await get_temporal_client()
        await client.workflow_service.get_system_info()
        return web.Response(text="ready")
    except Exception as e:
        return web.Response(status=503, text=f"not ready: {str(e)}")

async def metrics(request: web.Request) -> web.Response:
    """Prometheus metrics endpoint."""
    from prometheus_client import generate_latest
    return web.Response(
        body=generate_latest(),
        content_type="text/plain"
    )

async def start_workflow() -> None:
    """Start a single workflow execution."""
    try:
        client = await get_temporal_client()
        
        # Start your workflow here
        handle = await client.start_workflow(
            "GreetingWorkflow",
            "World",
            id=f"greeting-{asyncio.datetime.now().timestamp()}",
            task_queue=os.getenv("TEMPORAL_TASKQUEUE", "greeting-tasks"),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(minutes=1),
                maximum_attempts=3,
            )
        )
        
        workflows_started.inc()
        print(f"Started workflow: {handle.id}")
        
    except Exception as e:
        workflow_failures.inc()
        print(f"Failed to start workflow: {str(e)}")
        raise

async def run_workflow_starter() -> None:
    """Main loop for starting workflows periodically."""
    interval = int(os.getenv("WORKFLOW_INTERVAL_SECONDS", "300"))
    
    while True:
        try:
            await start_workflow()
        except Exception as e:
            print(f"Error in workflow starter: {str(e)}")
        
        await asyncio.sleep(interval)

async def create_app() -> web.Application:
    """Create and configure the web application."""
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/ready', readiness_check)
    app.router.add_get('/metrics', metrics)
    return app

async def main() -> None:
    """Main entry point for the orchestrator."""
    # Start Prometheus metrics server
    start_http_server(port=9090)
    
    # Create web app for health checks
    app = await create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    
    # Run everything together
    await asyncio.gather(
        site.start(),
        run_workflow_starter()
    )

if __name__ == "__main__":
    asyncio.run(main())
