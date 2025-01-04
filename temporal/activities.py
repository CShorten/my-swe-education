from datetime import datetime
from temporalio import activity

@activity.defn
async def say_hello(name: str) -> str:
    # Activities can do "real work" like API calls, DB operations, etc.
    # This is a dummy example that just returns a greeting
    current_time = datetime.now().strftime("%H:%M:%S")
    return f"Hello {name}! Activity executed at {current_time}"

@activity.defn
async def say_goodbye(name: str) -> str:
    return f"Goodbye {name}! Hope to see you again!"
