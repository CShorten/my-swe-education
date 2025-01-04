# Temporal Notes - Overview

## Core Mental Models

### The Director-Actor Analogy
Think of Temporal as a theater production:
- Workflows are directors - they coordinate and make decisions but never perform
- Activities are actors - they do all the actual work on stage
- The script (workflow code) is deterministic and repeatable
- If the theater loses power (system crash), everyone can resume exactly where they left off

### The Brain and Hands
Another powerful way to think about it:
- Workflows are the brain - they decide what needs to be done
- Activities are the hands - they perform the actual work
- Just as you wouldn't try to lift a box with your brain, never try to do real work in a workflow
- Just as hands don't make strategic decisions, activities shouldn't contain complex orchestration logic

## Critical Rules to Remember

### The Golden Rule of Workflows
Workflows must be perfectly repeatable. This means workflows cannot:
- Make HTTP requests or API calls
- Read from databases
- Access files
- Generate random numbers
- Get the current time directly
- Perform any non-deterministic operations

### The Golden Rule of Activities
Activities must be idempotent when possible. This means:
- Activities should handle being run multiple times safely
- If an activity fails, it might run again from the start
- Activities should check for and handle duplicate executions gracefully

## Comparisons with Other Systems

### vs. MapReduce
- MapReduce is about transforming large datasets through identical workers
- Temporal is about orchestrating complex processes through distinct steps
- MapReduce splits data, Temporal splits processes
- MapReduce handles state implicitly, Temporal handles it explicitly

### vs. Apache Spark
- Spark unifies transformation description and execution
- Temporal strictly separates coordination from execution
- Spark thinks in terms of data transformations
- Temporal thinks in terms of process orchestration

## State Management

### Workflow State
- Automatically persisted
- Survives system crashes
- Should only contain coordination data
- Must be deterministic
- Examples: status flags, counters, decision points

### Activity State
- Transient and not persisted
- May need to handle duplicate executions
- Can contain any data needed for execution
- Can be non-deterministic
- Examples: API responses, database records, file contents

## Error Handling Patterns

### Workflow-Level Recovery
```python
@workflow.defn
class ResilientWorkflow:
    def __init__(self):
        self.retry_count = 0  # Persisted across crashes

    @workflow.run
    async def run(self):
        try:
            await self.main_logic()
        except Exception:
            if self.retry_count < 3:
                self.retry_count += 1
                return await self.run()  # Retry entire workflow
            await self.compensation_logic()
```

### Activity-Level Recovery
```python
# Configure retry policies for transient failures
retry_policy = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(minutes=1),
    maximum_attempts=3
)

# Apply policy to activity execution
result = await workflow.execute_activity(
    process_order,
    order_id,
    retry_policy=retry_policy,
    start_to_close_timeout=timedelta(minutes=5)
)
```

## System Integration Patterns

### External System Integration
- Always interact with external systems in activities, never in workflows
- Use timeouts to prevent activities from hanging indefinitely
- Consider idempotency tokens for critical operations
- Keep external system credentials and configuration in activity layer

### Workflow-to-Workflow Communication
- Use child workflows for complex sub-processes
- Use signals for asynchronous updates
- Use queries for reading workflow state
- Consider saga patterns for distributed transactions

## Quick Decision Guide

Use Temporal when you need:
1. Long-running processes with multiple steps
2. Complex error handling and compensation logic
3. Integration of multiple services
4. Reliable state management across failures
5. Audit trails of business processes

Use alternatives when:
1. Primarily doing data transformations (→ Spark)
2. Need simple batch processing (→ MapReduce)
3. Building stateless services (→ Traditional microservices)
4. Handling real-time streaming (→ Kafka/Flink)

This mental model and reference guide should help you make the right architectural decisions when working with Temporal and understand how it fits into the broader distributed systems landscape.
