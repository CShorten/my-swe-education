# The Essential Relationship Between Workflows and Activities in Temporal

## The Core Mental Model

Think of a workflow as a director orchestrating a complex play, while activities are the individual actors performing specific scenes. The director (workflow) doesn't actually act in the play – instead, they coordinate when and how each actor (activity) performs their part. This distinction is absolutely fundamental to understanding Temporal.

Let's make this concrete with a simple example:

```python
@workflow.defn
class ShippingWorkflow:
    @workflow.run
    async def run(self, order_id: str) -> str:
        # The workflow is like a director giving stage directions
        # It doesn't do the actual work - it coordinates the activities

        # First scene: Check inventory
        inventory_result = await workflow.execute_activity(
            check_inventory,
            order_id,
            start_to_close_timeout=timedelta(minutes=5)
        )

        # Second scene: Process payment
        await workflow.execute_activity(
            process_payment,
            order_id,
            start_to_close_timeout=timedelta(minutes=5)
        )

        # Final scene: Ship the order
        await workflow.execute_activity(
            ship_order,
            order_id,
            start_to_close_timeout=timedelta(hours=1)
        )
```

## The Critical Distinctions

### Workflows Cannot Do Real Work

This is perhaps the most important rule: Workflows should never perform actual business operations. They cannot:
- Make HTTP requests
- Read from databases
- Write to files
- Generate random numbers
- Even check the current time directly

Why? Because workflows must be perfectly repeatable. If your application crashes, Temporal needs to replay your workflow exactly as it happened before. This is only possible if workflows stick to pure coordination logic.

Here's what NOT to do in a workflow:

```python
@workflow.defn
class IncorrectWorkflow:
    @workflow.run
    async def run(self, order_id: str) -> str:
        # WRONG: Never do this in a workflow!
        response = requests.get(f"https://api.example.com/orders/{order_id}")
        
        # WRONG: Don't generate random numbers in workflows!
        tracking_number = random.randint(1000, 9999)
```

Instead, all real work must happen in activities:

```python
@activity.defn
async def fetch_order_details(order_id: str) -> dict:
    # Activities CAN do real work
    response = requests.get(f"https://api.example.com/orders/{order_id}")
    return response.json()

@activity.defn
async def generate_tracking_number() -> str:
    # Activities CAN generate random numbers
    return str(random.randint(1000, 9999))
```

### Workflows Are Durable, Activities Are Transient

Think of workflows as having perfect memory. If your server crashes, the workflow will resume exactly where it left off, remembering all its previous decisions. Activities, on the other hand, must be prepared to run multiple times.

Consider this example:

```python
@workflow.defn
class DurableWorkflow:
    def __init__(self):
        self.total_amount = 0  # This state persists across crashes

    @workflow.run
    async def run(self, items: List[str]) -> float:
        for item in items:
            # Even if the server crashes, we'll resume at the exact right item
            price = await workflow.execute_activity(
                calculate_price,
                item,
                start_to_close_timeout=timedelta(minutes=1)
            )
            self.total_amount += price  # This addition will never be lost
        return self.total_amount

@activity.defn
async def calculate_price(item: str) -> float:
    # This activity might run multiple times for the same item
    # It must be idempotent - running it twice should be safe
    db = connect_to_database()
    return await db.get_price(item)
```

## The Dance Between Workflows and Activities

Understanding this relationship is crucial: Workflows orchestrate the high-level flow while delegating all actual work to activities. Here's a more complex example that demonstrates this dance:

```python
@workflow.defn
class OrderProcessingWorkflow:
    def __init__(self):
        self.status = "CREATED"
        self.retry_count = 0

    @workflow.run
    async def run(self, order_id: str) -> str:
        # Workflow logic is about making decisions and coordinating
        try:
            # Delegate actual inventory check to an activity
            inventory_status = await workflow.execute_activity(
                check_inventory,
                order_id,
                start_to_close_timeout=timedelta(minutes=5)
            )

            if inventory_status == "IN_STOCK":
                # Coordinate payment processing
                payment_result = await workflow.execute_activity(
                    process_payment,
                    order_id,
                    start_to_close_timeout=timedelta(minutes=5)
                )
                
                if payment_result == "SUCCESS":
                    self.status = "PAID"
                    
                    # Coordinate shipping
                    await workflow.execute_activity(
                        ship_order,
                        order_id,
                        start_to_close_timeout=timedelta(hours=1)
                    )
                    return "Order completed successfully"
            else:
                # Coordinate backorder process
                await workflow.execute_activity(
                    create_backorder,
                    order_id,
                    start_to_close_timeout=timedelta(minutes=5)
                )
                return "Order backordered"
                
        except Exception as e:
            self.retry_count += 1  # This counter persists across crashes
            if self.retry_count <= 3:
                # Retry the entire workflow
                return await self.run(order_id)
            else:
                # Coordinate failure handling
                await workflow.execute_activity(
                    notify_failure,
                    order_id,
                    start_to_close_timeout=timedelta(minutes=5)
                )
                return "Order failed"
```

## The Key Takeaway

If you remember nothing else, remember this: Workflows are for coordination, Activities are for doing. Every time you write a workflow, ask yourself: "Am I trying to do real work here?" If the answer is yes, that logic belongs in an activity instead.

This separation might feel restrictive at first, but it's what enables Temporal's powerful durability guarantees. By keeping workflows pure and delegating all real work to activities, you create systems that can recover from virtually any failure without losing track of their progress or making incorrect decisions.

Think of it this way: Workflows are the brains, Activities are the hands. The brain decides what to do, but it's the hands that actually pick things up and move them around. Just as you wouldn't try to lift a box with your brain, you shouldn't try to do real work in a workflow. Let each part play its proper role, and you'll build robust, maintainable distributed systems.
