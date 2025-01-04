from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

# Import our activity functions
from activities import say_hello, say_goodbye

@workflow.defn
class GreetingWorkflow:
    @workflow.run
    async def run(self, name: str) -> list[str]:
        # Define a retry policy for our activities
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(minutes=1),
            maximum_attempts=3,
        )
        
        # Execute our first activity
        hello_result = await workflow.execute_activity(
            say_hello,
            name,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
        )
        
        # Execute our second activity
        goodbye_result = await workflow.execute_activity(
            say_goodbye,
            name,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
        )
        
        # Return both results
        return [hello_result, goodbye_result]
