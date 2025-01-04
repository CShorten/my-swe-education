import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from activities import say_hello, say_goodbye
from workflows import GreetingWorkflow

async def main():
    # Connect client
    client = await Client.connect(
        "foo.bar.temporal.cloud",  # Your Temporal Cloud namespace URL
        namespace="your-namespace",
        ssl=True,  # Required for Temporal Cloud
        identity="python-worker",
        tls_cert_path="/path/to/cert.pem",  # Your certificate path
        tls_key_path="/path/to/key.pem",    # Your private key path
    )

    # Run the worker
    worker = Worker(
        client,
        task_queue="greeting-tasks",
        workflows=[GreetingWorkflow],
        activities=[say_hello, say_goodbye],
    )
    
    print("Worker started, press Ctrl+C to exit")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
