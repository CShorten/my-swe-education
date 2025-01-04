import asyncio
from temporalio.client import Client
from workflows import GreetingWorkflow

async def main():
    # Connect client
    client = await Client.connect(
        "foo.bar.temporal.cloud",  # Your Temporal Cloud namespace URL
        namespace="your-namespace",
        ssl=True,  # Required for Temporal Cloud
        identity="python-starter",
        tls_cert_path="/path/to/cert.pem",  # Your certificate path
        tls_key_path="/path/to/key.pem",    # Your private key path
    )

    # Start a workflow execution
    handle = await client.start_workflow(
        GreetingWorkflow.run,
        "World",  # This is the 'name' parameter for our workflow
        id="greeting-workflow-1",
        task_queue="greeting-tasks",
    )
    
    # Wait for workflow completion
    result = await handle.result()
    print(f"Workflow complete! Results: {result}")

if __name__ == "__main__":
    asyncio.run(main())
