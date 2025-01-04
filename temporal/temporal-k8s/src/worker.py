import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker
from activities import say_hello, say_goodbye
from workflows import GreetingWorkflow

# Read configuration from environment
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE")
TEMPORAL_TASKQUEUE = os.getenv("TEMPORAL_TASKQUEUE")
CERT_PATH = "/etc/temporal/certs/tls.crt"
KEY_PATH = "/etc/temporal/certs/tls.key"

async def main():
    # Create client
    client = await Client.connect(
        TEMPORAL_HOST,
        namespace=TEMPORAL_NAMESPACE,
        ssl=True,
        identity="python-worker",
        tls_cert_path=CERT_PATH,
        tls_key_path=KEY_PATH,
    )

    # Run worker
    worker = Worker(
        client,
        task_queue=TEMPORAL_TASKQUEUE,
        workflows=[GreetingWorkflow],
        activities=[say_hello, say_goodbye],
    )
    
    print(f"Worker started, connecting to {TEMPORAL_HOST}")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())