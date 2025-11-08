# Cost-Based Query Planning: From Relational to Semantic Operators

## Table of Contents
1. [Introduction](#introduction)
2. [Classical Cost-Based Optimization](#classical-cost-based-optimization)
3. [The Cascades Framework](#the-cascades-framework)
4. [Cost-Based Planning for Semantic Operators](#cost-based-planning-for-semantic-operators)
5. [Palimpzest's Abacus Optimizer](#palimpzests-abacus-optimizer)
6. [Challenges and Future Directions](#challenges-and-future-directions)

---

## Introduction

Cost-based query planning is a foundational technique in database systems that automatically selects the most efficient way to execute a query. Rather than using fixed rules, cost-based optimizers estimate the "cost" of different execution strategies and choose the cheapest one. This approach has been the backbone of relational database performance for decades and is now being adapted for the emerging class of semantic query processing engines.

### What is "Cost"?

In traditional databases, cost typically represents:
- **I/O operations:** Reading data from disk
- **CPU cycles:** Processing and comparing data
- **Memory usage:** Sorting and joining operations
- **Network transfer:** In distributed systems

In semantic query processing, cost additionally includes:
- **LLM invocations:** Number of API calls to language models
- **Token consumption:** Input and output tokens processed
- **Monetary fees:** Actual dollar cost of LLM usage
- **Latency:** Time waiting for LLM responses

The fundamental insight remains the same: **enumerate possible execution plans, estimate their costs, and choose the best one.**

---

## Classical Cost-Based Optimization

### The Query Optimization Problem

Given a SQL query, there are often many logically equivalent ways to execute it. Consider:

```sql
SELECT *
FROM Employees E, Departments D, Projects P
WHERE E.dept_id = D.dept_id
  AND E.emp_id = P.emp_id
  AND D.location = 'NYC'
  AND P.budget > 100000
```

**Possible execution plans:**
1. Join E and D, filter by location, then join with P
2. Filter D by location first, then join with E, then join with P
3. Filter P by budget first, join with E, then join with filtered D
4. Many more combinations...

Each plan has different costs depending on:
- Table sizes
- Index availability
- Join algorithms (nested loop, hash join, sort-merge)
- Filter selectivity

### The Cost Model

Classical optimizers use **statistical information** to estimate costs:

```
Cost(Plan) = Cost(I/O) + Cost(CPU)

Cost(I/O) = (# pages read) × (cost per page)
Cost(CPU) = (# tuples processed) × (cost per tuple)
```

**Example calculation:**

```
Query: SELECT * FROM Orders WHERE customer_id = 12345

Plan 1: Sequential scan
- Read all pages: 10,000 pages × 1 ms = 10,000 ms
- Check all rows: 1,000,000 rows × 0.001 ms = 1,000 ms
- Total: 11,000 ms

Plan 2: Index scan (if index exists on customer_id)
- Read index: 3 pages × 1 ms = 3 ms
- Read matching data: 10 pages × 1 ms = 10 ms
- Check matching rows: 100 rows × 0.001 ms = 0.1 ms
- Total: 13.1 ms

Winner: Plan 2 (with index)
```

### Key Optimization Techniques

#### 1. **Filter Pushdown**

**Bad plan:**
```
1. Join Employees and Projects (1M × 500K = 500B comparisons)
2. Filter result where budget > 100000
```

**Good plan:**
```
1. Filter Projects where budget > 100000 (reduces to 50K rows)
2. Join Employees and filtered Projects (1M × 50K = 50B comparisons)
```

**Cost reduction:** 10× fewer operations

#### 2. **Join Reordering**

Given three tables to join, there are multiple orderings:

```
Tables:
- Customers: 1M rows
- Orders: 10M rows  
- OrderItems: 100M rows

Query: SELECT * FROM Customers C, Orders O, OrderItems I
WHERE C.id = O.customer_id AND O.id = I.order_id
```

**Bad order:** Start with the largest tables
```
1. Join Orders ⋈ OrderItems = 100M results
2. Join with Customers = filter 100M rows
Cost: ~100M operations
```

**Good order:** Start with smallest, build up
```
1. Join Customers ⋈ Orders = 10M results
2. Join with OrderItems = filter 10M rows  
Cost: ~10M operations
```

**Cost reduction:** 10× fewer operations

#### 3. **Join Algorithm Selection**

Different join algorithms for different scenarios:

```
Nested Loop Join:
- Best when: One table is very small
- Cost: O(n × m)
- Example: 100 × 1M = 100M comparisons

Hash Join:
- Best when: Medium-sized tables that fit in memory
- Cost: O(n + m)
- Example: 100 + 1M = 1.0001M operations

Sort-Merge Join:
- Best when: Large tables, especially if pre-sorted
- Cost: O(n log n + m log m + n + m)
- Example: Effective when data already has some ordering
```

### Statistics and Cardinality Estimation

Optimizers maintain statistics about data:

```sql
-- Table statistics
Table: Orders
Rows: 1,000,000
Pages: 10,000
Average row size: 200 bytes

-- Column statistics  
Column: order_date
Distinct values: 365
Min: 2024-01-01
Max: 2024-12-31
Histogram: [showing distribution across date ranges]

Column: customer_id
Distinct values: 100,000
Null percentage: 0%
```

**Selectivity estimation:**

```sql
WHERE order_date = '2024-06-15'
Selectivity = 1 / distinct_values = 1/365 ≈ 0.27%
Estimated rows = 1,000,000 × 0.0027 = 2,740 rows

WHERE customer_id IN (SELECT id FROM PremiumCustomers)
-- Requires subquery estimation
If PremiumCustomers has 5,000 rows:
Estimated rows = 1,000,000 × (5,000/100,000) = 50,000 rows
```

---

## The Cascades Framework

The Cascades framework (Graefe, 1995) is a sophisticated architecture for query optimization that separates logical and physical planning. It's the foundation for many modern optimizers, including Palimpzest's Abacus optimizer.

### Core Concepts

#### 1. **Logical vs Physical Operators**

**Logical operators** describe *what* to compute:
```
LogicalFilter(predicate: "price > 100")
LogicalJoin(condition: "A.id = B.id")
LogicalSort(column: "name")
```

**Physical operators** describe *how* to compute:
```
PhysicalFilter_Sequential(predicate: "price > 100")
PhysicalFilter_Index(predicate: "price > 100", index: "price_idx")

PhysicalJoin_NestedLoop(condition: "A.id = B.id")
PhysicalJoin_Hash(condition: "A.id = B.id")
PhysicalJoin_SortMerge(condition: "A.id = B.id")
```

#### 2. **Transformation Rules**

**Logical transformations** create equivalent logical plans:

```
Rule: Join Commutativity
A ⋈ B  ≡  B ⋈ A

Rule: Join Associativity  
(A ⋈ B) ⋈ C  ≡  A ⋈ (B ⋈ C)

Rule: Filter Pushdown
σ_p(A ⋈ B)  ≡  σ_p(A) ⋈ B  (if p only references A)

Rule: Filter Merge
σ_p1(σ_p2(A))  ≡  σ_(p1 ∧ p2)(A)
```

**Implementation rules** convert logical to physical:

```
LogicalJoin → PhysicalJoin_Hash
LogicalJoin → PhysicalJoin_NestedLoop
LogicalJoin → PhysicalJoin_SortMerge
```

#### 3. **The MEMO Structure**

Cascades uses a compact representation called MEMO (Multi-Expression Optimization) to store equivalent plans:

```
Group 1: [Scan(Employees)]
  Physical: SeqScan(Employees) - Cost: 1000
  Physical: IndexScan(Employees, emp_id_idx) - Cost: 50

Group 2: [Filter(Group1, dept='Sales')]
  Physical: Filter_Sequential(Group1) - Cost: 1050
  Physical: Filter_Index(Group1, dept_idx) - Cost: 30

Group 3: [Join(Group2, Departments)]
  Physical: HashJoin(Group2, Departments) - Cost: 1100
  Physical: NestedLoopJoin(Group2, Departments) - Cost: 2500
  Physical: SortMergeJoin(Group2, Departments) - Cost: 1300
```

Each group represents logically equivalent expressions. The optimizer explores combinations and prunes expensive paths.

### The Optimization Algorithm

```python
def optimize(logical_expr, required_properties):
    """
    Cascades optimization algorithm
    
    Args:
        logical_expr: Logical query expression
        required_properties: Output requirements (sort order, etc.)
    
    Returns:
        Best physical plan satisfying requirements
    """
    # Check if we've already optimized this
    group = memo.find_or_create_group(logical_expr)
    
    if group.has_plan(required_properties):
        return group.get_best_plan(required_properties)
    
    best_plan = None
    best_cost = INFINITY
    
    # Apply logical transformation rules
    for rule in logical_rules:
        if rule.matches(logical_expr):
            transformed = rule.apply(logical_expr)
            plan = optimize(transformed, required_properties)
            
            if plan.cost < best_cost:
                best_cost = plan.cost
                best_plan = plan
    
    # Apply implementation rules (logical → physical)
    for impl_rule in implementation_rules:
        if impl_rule.matches(logical_expr):
            physical_op = impl_rule.apply(logical_expr)
            
            # Recursively optimize children
            child_plans = []
            for child in physical_op.children:
                child_plan = optimize(child, physical_op.required_child_properties)
                child_plans.append(child_plan)
            
            # Compute cost of this physical operator
            cost = physical_op.compute_cost(child_plans)
            
            if cost < best_cost:
                best_cost = cost
                best_plan = PhysicalPlan(physical_op, child_plans)
    
    # Memoize result
    group.add_plan(required_properties, best_plan, best_cost)
    
    return best_plan
```

### Example Optimization Trace

Given query:
```sql
SELECT * FROM A, B, C
WHERE A.x = B.x AND B.y = C.y AND A.z > 100
```

**Phase 1: Logical exploration**
```
Initial:
  Join(Join(Filter(A, z>100), B), C)

After Join Reordering:
  Join(A, Join(B, C))
  Join(Filter(A, z>100), Join(B, C))
  Join(Join(A, B), Filter(C, ...))  [not valid - filter on A]

After Filter Pushdown:
  Join(Join(Filter(A, z>100), B), C)  [original]
```

**Phase 2: Physical implementation**
```
Option 1:
  HashJoin(
    HashJoin(
      SeqScan + Filter(A),
      SeqScan(B)
    ),
    SeqScan(C)
  )
  Cost: 1000 + 500 + 300 = 1800

Option 2:
  HashJoin(
    NestedLoopJoin(
      IndexScan(A, z_idx),
      SeqScan(B)
    ),
    SeqScan(C)
  )
  Cost: 50 + 400 + 300 = 750  ← Winner!

Option 3:
  SortMergeJoin(
    SortMergeJoin(
      IndexScan(A, z_idx),
      Sort(SeqScan(B))
    ),
    Sort(SeqScan(C))
  )
  Cost: 50 + 550 + 350 = 950
```

**Result:** Optimizer chooses Option 2

### Pruning Strategies

To avoid exploring the entire search space:

**1. Cost-based pruning:**
```python
if current_partial_cost > best_complete_cost:
    return  # This path can't be better
```

**2. Property enforcement:**
```python
# If we need sorted output, don't explore unsorted plans
if required_properties.sort_order and not plan.is_sorted:
    return
```

**3. Interesting orders:**
```python
# Keep plans that produce useful sort orders for later joins
if plan.produces_interesting_order():
    memo.remember(plan)  # Even if not cheapest
```

---

## Cost-Based Planning for Semantic Operators

### The New Challenge

Traditional cost-based optimization assumes:
1. **Deterministic costs:** Same query, same cost every time
2. **Fast operations:** Microseconds to milliseconds
3. **Simple cost model:** I/O + CPU
4. **Perfect correctness:** 2 + 2 always equals 4

Semantic operators break all these assumptions:

```sql
-- Traditional filter: deterministic, fast, cheap
SELECT * FROM Products WHERE price > 100
-- Cost: ~10ms, $0

-- Semantic filter: stochastic, slow, expensive  
SELECT * FROM Products WHERE AI.IF(image, 'shows a red product')
-- Cost: ~60 seconds, $0.50 per query
-- Different models give different results!
```

### The Multi-Dimensional Cost Space

Semantic query planning must optimize across **three dimensions simultaneously:**

```
Traditional:    Cost (I/O + CPU)

Semantic:       Cost (monetary $)
                Quality (accuracy)
                Latency (seconds)
```

**Example tradeoff:**

```
Query: Classify 1000 product images by color

Option A: gpt-4o (powerful model)
- Cost: $5.00
- Quality: 95% accuracy
- Latency: 120 seconds

Option B: gpt-4o-mini (smaller model)  
- Cost: $0.50
- Quality: 88% accuracy
- Latency: 60 seconds

Option C: CLIP embeddings + classifier (no LLM)
- Cost: $0.01
- Quality: 82% accuracy
- Latency: 5 seconds

Which is "best"? Depends on user requirements!
```

### Physical Operator Alternatives

For each logical semantic operator, there are multiple physical implementations:

#### Semantic Filter Implementations

```python
# Implementation 1: Direct LLM call
def filter_llm_full(data, predicate, model="gpt-4o"):
    results = []
    for item in data:
        prompt = f"Does this satisfy: {predicate}? Answer yes/no.\n{item}"
        response = call_llm(model, prompt)
        if response == "yes":
            results.append(item)
    return results
    
# Cost: High ($), Quality: High, Latency: High

# Implementation 2: Smaller model
def filter_llm_mini(data, predicate, model="gpt-4o-mini"):
    # Same as above but cheaper model
    # Cost: Medium ($), Quality: Medium, Latency: Medium

# Implementation 3: Embedding similarity
def filter_embedding(data, predicate, threshold=0.8):
    target_embedding = embed(predicate)
    results = []
    for item in data:
        item_embedding = embed(item)
        if cosine_similarity(item_embedding, target_embedding) > threshold:
            results.append(item)
    return results
    
# Cost: Low ($), Quality: Lower, Latency: Low

# Implementation 4: Hybrid approach
def filter_hybrid(data, predicate, model="gpt-4o"):
    # Stage 1: Embedding filter (cheap)
    candidates = filter_embedding(data, predicate, threshold=0.6)
    
    # Stage 2: LLM verification (expensive, but fewer items)
    results = filter_llm_full(candidates, predicate, model)
    return results
    
# Cost: Medium ($), Quality: High, Latency: Medium
```

#### Semantic Join Implementations

```python
# Implementation 1: Cartesian product with LLM
def join_cartesian_llm(table_a, table_b, condition):
    results = []
    for a in table_a:
        for b in table_b:
            if llm_check(condition, a, b):
                results.append((a, b))
    return results
    
# Cost: n×m LLM calls - VERY expensive!

# Implementation 2: Embedding-filtered LLM
def join_embedding_filtered(table_a, table_b, condition):
    embeddings_a = [embed(a) for a in table_a]
    embeddings_b = [embed(b) for b in table_b]
    
    candidates = []
    for i, a in enumerate(table_a):
        for j, b in enumerate(table_b):
            if cosine_similarity(embeddings_a[i], embeddings_b[j]) > 0.7:
                candidates.append((a, b))
    
    results = []
    for (a, b) in candidates:
        if llm_check(condition, a, b):
            results.append((a, b))
    
    return results
    
# Cost: Reduced by ~10-100× depending on data

# Implementation 3: Batched LLM calls
def join_batched(table_a, table_b, condition, batch_size=10):
    results = []
    for batch_a in batches(table_a, batch_size):
        for batch_b in batches(table_b, batch_size):
            prompt = f"""
            Find all matching pairs where {condition}
            Table A: {batch_a}
            Table B: {batch_b}
            Return: [(a_idx, b_idx), ...]
            """
            matches = llm_call(prompt)
            results.extend(matches)
    return results
    
# Cost: Reduced by batch_size² (e.g., 100× with batch=10)
# Quality: May be lower due to complex prompt
```

### Cost Models for Semantic Operators

#### Simple Cost Model

```python
def estimate_cost(physical_plan):
    cost = 0
    
    for operator in physical_plan:
        if operator.type == "LLM_CALL":
            # Model-specific pricing
            input_tokens = estimate_input_tokens(operator)
            output_tokens = estimate_output_tokens(operator)
            
            cost += (input_tokens * MODEL_INPUT_PRICE + 
                    output_tokens * MODEL_OUTPUT_PRICE)
        
        elif operator.type == "EMBEDDING":
            # Embedding model pricing (usually cheaper)
            items = estimate_items_processed(operator)
            cost += items * EMBEDDING_PRICE
        
        elif operator.type == "TRADITIONAL":
            # Negligible compared to LLM costs
            cost += 0
    
    return cost
```

**Example calculation:**

```sql
SELECT * FROM Products 
WHERE AI.IF(description, 'mentions sustainability')
  AND price < 100
```

```python
# Plan 1: LLM filter first, then price filter
cost_plan1 = (
    1000 items × 50 input tokens × $0.00001 +  # LLM filter
    1000 items × 5 output tokens × $0.00003 +   # LLM outputs
    0                                             # Price filter (free)
) = $0.65

# Plan 2: Price filter first, then LLM filter  
cost_plan2 = (
    0 +                                           # Price filter (free)
    200 items × 50 input tokens × $0.00001 +     # LLM on 20% of data
    200 items × 5 output tokens × $0.00003
) = $0.13

# Plan 2 is 5× cheaper!
```

#### Quality Estimation

Quality is harder to estimate without ground truth:

```python
def estimate_quality(physical_plan, operator):
    """
    Estimate quality based on:
    1. Historical performance of similar operators
    2. Model capabilities
    3. Prompt complexity
    """
    
    if operator.type == "FULL_LLM":
        base_quality = MODEL_QUALITY[operator.model]  # e.g., 0.95 for gpt-4o
        
        # Adjust for prompt complexity
        if operator.prompt_length > 500:
            base_quality *= 0.98  # Longer prompts may confuse model
        
        # Adjust for task difficulty
        if operator.task in ["classification", "filter"]:
            return base_quality
        elif operator.task == "join":
            return base_quality * 0.90  # Joins are harder
        elif operator.task == "extraction":
            return base_quality * 0.85  # Extraction is hardest
    
    elif operator.type == "EMBEDDING":
        # Embeddings are fast but less accurate
        return 0.75
    
    elif operator.type == "HYBRID":
        # Combination of embedding filter + LLM verification
        embedding_recall = 0.95  # % of true positives retained
        llm_precision = 0.98
        return embedding_recall * llm_precision  # = 0.93
```

#### Latency Estimation

```python
def estimate_latency(physical_plan, parallelism=20):
    """
    Estimate wall-clock time considering parallelism
    """
    
    latency = 0
    
    for operator in physical_plan:
        items = estimate_items_processed(operator)
        
        if operator.type == "LLM_CALL":
            avg_llm_latency = 2.0  # seconds per call
            
            # With parallelism, we can do multiple calls simultaneously
            sequential_time = items * avg_llm_latency
            parallel_time = sequential_time / parallelism
            
            latency += parallel_time
        
        elif operator.type == "EMBEDDING":
            # Embeddings are fast, even for many items
            latency += items * 0.001  # 1ms per item
        
        elif operator.type == "TRADITIONAL":
            # Traditional operators are negligible
            latency += 0.01
    
    return latency
```

**Example:**

```python
# Query: Filter 1000 items with LLM
items = 1000
llm_latency_per_call = 2.0  # seconds

# Sequential execution
sequential_latency = 1000 × 2.0 = 2000 seconds = 33 minutes!

# Parallel execution (20 concurrent calls)
parallel_latency = 2000 / 20 = 100 seconds = 1.7 minutes

# Embedding + LLM hybrid (filter to 200 candidates first)
hybrid_latency = (
    1000 × 0.001 +      # Embedding: 1 second
    200 × 2.0 / 20      # LLM on 200 items: 20 seconds
) = 21 seconds

# Hybrid is ~5× faster than parallel LLM!
```

### Optimization Objectives

Unlike traditional optimizers with a single cost metric, semantic query optimizers need **multi-objective optimization:**

```python
class OptimizationObjective:
    """
    User-specified optimization goal
    """
    
    def __init__(self, objective, constraints):
        self.objective = objective      # What to optimize
        self.constraints = constraints  # Hard limits
    
# Example objectives:

# 1. Minimize cost, subject to quality constraint
obj1 = OptimizationObjective(
    objective="MINIMIZE_COST",
    constraints={"quality": 0.90, "latency": 120}
)

# 2. Maximize quality, subject to cost constraint
obj2 = OptimizationObjective(
    objective="MAXIMIZE_QUALITY",
    constraints={"cost": 5.00, "latency": 60}
)

# 3. Minimize latency, subject to quality and cost
obj3 = OptimizationObjective(
    objective="MINIMIZE_LATENCY",
    constraints={"quality": 0.85, "cost": 2.00}
)
```

---

## Palimpzest's Abacus Optimizer

Palimpzest implements a sophisticated cost-based optimizer called **Abacus**, which is specifically designed for semantic operators. It's modeled after the Cascades framework but adapted for the unique challenges of LLM-based query processing.

### Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│              User Query (Python)                     │
│  df.filter(...).join(...).map(...)                  │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│            Logical Plan Generation                   │
│  LogicalFilter → LogicalJoin → LogicalMap           │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│              Abacus Optimizer                        │
│  ┌──────────────────────────────────────────────┐  │
│  │  Phase 1: Enumerate Physical Plans          │  │
│  │  - Generate all valid implementations       │  │
│  │  - Apply transformation rules               │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │  Phase 2: Sample & Measure                  │  │
│  │  - Run operators on data sample             │  │
│  │  - Measure cost, quality, latency           │  │
│  │  - Use ground truth or LLM judge            │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │  Phase 3: Build Cost Model                  │  │
│  │  - Estimate full-data performance           │  │
│  │  - Extrapolate from samples                 │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │  Phase 4: Select Best Plan                  │  │
│  │  - Choose plan satisfying objective         │  │
│  │  - Respect user constraints                 │  │
│  └──────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│          Execute Optimized Plan                      │
│  Run selected physical operators on full data        │
└─────────────────────────────────────────────────────┘
```

### Physical Operator Enumeration

Abacus maintains a catalog of physical operators for each logical operator:

```python
PHYSICAL_OPERATORS = {
    "LogicalFilter": [
        PhysicalFilter_LLM_Full(model="gpt-4o"),
        PhysicalFilter_LLM_Full(model="gpt-4o-mini"),
        PhysicalFilter_LLM_FewShot(model="gpt-4o", examples=5),
        PhysicalFilter_Embedding(model="e5-base-v2", threshold=0.8),
        PhysicalFilter_Embedding(model="e5-base-v2", threshold=0.7),
        PhysicalFilter_Hybrid(
            stage1=PhysicalFilter_Embedding(),
            stage2=PhysicalFilter_LLM_Full()
        ),
    ],
    
    "LogicalJoin": [
        PhysicalJoin_Cartesian_LLM(model="gpt-4o"),
        PhysicalJoin_Cartesian_LLM(model="gpt-4o-mini"),
        PhysicalJoin_Embedding_Filtered(
            embedding_model="clip-vit-b-32",
            llm_model="gpt-4o",
            threshold=0.8
        ),
        PhysicalJoin_Batched(model="gpt-4o", batch_size=10),
        PhysicalJoin_Batched(model="gpt-4o", batch_size=20),
    ],
    
    "LogicalMap": [
        PhysicalMap_LLM(model="gpt-4o"),
        PhysicalMap_LLM(model="gpt-4o-mini"),
        PhysicalMap_LLM_Structured(model="gpt-4o", schema=output_schema),
    ],
    
    # ... more operators
}
```

### Sampling-Based Cost Estimation

Unlike traditional optimizers that use statistics, Abacus **actually runs** operators on a sample of data:

```python
def estimate_operator_cost(physical_op, data_sample, ground_truth=None):
    """
    Run physical operator on sample and measure performance
    
    Args:
        physical_op: Physical operator to test
        data_sample: Small subset of data (e.g., 100 rows)
        ground_truth: Optional labels for quality assessment
    
    Returns:
        (cost, quality, latency) tuple
    """
    
    # Measure actual execution
    start_time = time.time()
    start_cost = get_llm_cost_so_far()
    
    result = physical_op.execute(data_sample)
    
    end_time = time.time()
    end_cost = get_llm_cost_so_far()
    
    # Compute metrics
    latency = end_time - start_time
    cost = end_cost - start_cost
    
    # Assess quality
    if ground_truth is not None:
        # Compare with ground truth labels
        quality = compute_accuracy(result, ground_truth)
    else:
        # Use LLM judge to assess quality
        quality = llm_judge_quality(result, physical_op.description)
    
    # Extrapolate to full dataset
    sample_size = len(data_sample)
    full_size = get_full_dataset_size()
    scaling_factor = full_size / sample_size
    
    estimated_cost = cost * scaling_factor
    estimated_latency = latency * scaling_factor
    # Quality typically doesn't scale with size
    estimated_quality = quality
    
    return (estimated_cost, estimated_quality, estimated_latency)
```

**Example sampling process:**

```python
# Original query: Filter 10,000 product descriptions
logical_plan = LogicalFilter(
    input=Products,
    predicate="mentions sustainability"
)

# Sample 100 random products
sample = Products.sample(100)

# Test different physical operators
results = {}

for phys_op in enumerate_physical_operators(logical_plan):
    cost, quality, latency = estimate_operator_cost(phys_op, sample)
    results[phys_op] = {
        "cost": cost,
        "quality": quality, 
        "latency": latency
    }

# Results might look like:
# PhysicalFilter_LLM(gpt-4o):        cost=$2.00, quality=0.95, latency=120s
# PhysicalFilter_LLM(gpt-4o-mini):   cost=$0.20, quality=0.88, latency=60s
# PhysicalFilter_Embedding:          cost=$0.01, quality=0.80, latency=5s
# PhysicalFilter_Hybrid:             cost=$0.50, quality=0.93, latency=30s
```

### Quality Assessment Strategies

Abacus supports multiple ways to assess quality:

#### 1. Ground Truth Labels

```python
# If user provides labeled examples
ground_truth = [
    {"text": "Eco-friendly bamboo toothbrush", "label": True},
    {"text": "Plastic disposable cups", "label": False},
    {"text": "Solar-powered charger", "label": True},
    # ... 100 labeled examples
]

def assess_quality_with_labels(result, ground_truth):
    """Compare operator output with known labels"""
    correct = 0
    for item, label in zip(result, ground_truth):
        if item.matches == label["label"]:
            correct += 1
    
    return correct / len(result)
```

#### 2. LLM Judge

```python
def assess_quality_with_judge(result, operator_description):
    """
    Use powerful LLM to judge quality of results
    """
    
    # Sample some results to judge
    sample_results = random.sample(result, min(50, len(result)))
    
    judgments = []
    for item in sample_results:
        prompt = f"""
        Operator task: {operator_description}
        
        Input: {item.input}
        Output: {item.output}
        
        Is this output correct and high-quality? Respond with:
        - CORRECT: Output is accurate
        - INCORRECT: Output is wrong
        - PARTIAL: Output is somewhat correct but incomplete
        """
        
        judgment = call_llm("gpt-4o", prompt)
        judgments.append(judgment)
    
    # Compute quality score
    correct = judgments.count("CORRECT")
    partial = judgments.count("PARTIAL")
    
    quality = (correct + 0.5 * partial) / len(judgments)
    return quality
```

#### 3. Prior Beliefs (Default)

```python
# If no ground truth or judge available, use prior knowledge
OPERATOR_QUALITY_PRIORS = {
    ("Filter", "gpt-4o"): 0.95,
    ("Filter", "gpt-4o-mini"): 0.88,
    ("Filter", "embedding"): 0.75,
    
    ("Join", "gpt-4o"): 0.90,
    ("Join", "gpt-4o-mini"): 0.82,
    ("Join", "embedding_filtered"): 0.85,
    
    # More conservative for complex tasks
    ("Map", "gpt-4o"): 0.85,
    ("Classify", "gpt-4o"): 0.92,
}

def assess_quality_with_priors(operator):
    """Use pre-defined quality estimates"""
    operator_type = operator.logical_type
    model = operator.model
    
    return OPERATOR_QUALITY_PRIORS.get(
        (operator_type, model),
        0.80  # Default conservative estimate
    )
```

### Plan Selection with Constraints

Once all physical plans are evaluated, Abacus selects the best one according to user objectives:

```python
def select_best_plan(plans, objective, constraints):
    """
    Choose optimal plan satisfying constraints
    
    Args:
        plans: List of (plan, cost, quality, latency) tuples
        objective: What to optimize (cost, quality, or latency)
        constraints: Hard limits on other metrics
    
    Returns:
        Best plan satisfying all constraints
    """
    
    # Filter plans that violate constraints
    valid_plans = []
    for plan, metrics in plans:
        if "quality" in constraints and metrics.quality < constraints["quality"]:
            continue
        if "cost" in constraints and metrics.cost > constraints["cost"]:
            continue
        if "latency" in constraints and metrics.latency > constraints["latency"]:
            continue
        
        valid_plans.append((plan, metrics))
    
    if not valid_plans:
        raise ValueError("No plan satisfies all constraints!")
    
    # Select best according to objective
    if objective == "MINIMIZE_COST":
        best_plan = min(valid_plans, key=lambda x: x[1].cost)
    
    elif objective == "MAXIMIZE_QUALITY":
        best_plan = max(valid_plans, key=lambda x: x[1].quality)
    
    elif objective == "MINIMIZE_LATENCY":
        best_plan = min(valid_plans, key=lambda x: x[1].latency)
    
    return best_plan[0]
```

**Example selection:**

```python
# User specifies: Maximize quality, but stay under $5 and 2 minutes

plans = [
    (Plan1, {"cost": 10.0, "quality": 0.98, "latency": 180}),  # Too expensive
    (Plan2, {"cost": 3.0,  "quality": 0.95, "latency": 90}),   # ✓ Valid
    (Plan3, {"cost": 0.5,  "quality": 0.85, "latency": 30}),   # ✓ Valid
    (Plan4, {"cost": 4.5,  "quality": 0.92, "latency": 150}),  # ✓ Valid
    (Plan5, {"cost": 2.0,  "quality": 0.88, "latency": 200}),  # Too slow
]

objective = "MAXIMIZE_QUALITY"
constraints = {"cost": 5.0, "latency": 120}

# Plan1 rejected: cost > $5
# Plan5 rejected: latency > 120s
# Among Plan2, Plan3, Plan4: Plan2 has highest quality (0.95)
# Winner: Plan2
```

### Complex Query Optimization

For multi-operator queries, Abacus explores combinations:

```python
# Query with two operators
query = df.filter(predicate1).map(transform)

# Logical plan
logical = LogicalMap(
    input=LogicalFilter(
        input=DataFrame,
        predicate=predicate1
    ),
    transform=transform
)

# Physical plan enumeration
filter_impls = [
    PhysicalFilter_LLM("gpt-4o"),
    PhysicalFilter_LLM("gpt-4o-mini"),
    PhysicalFilter_Embedding(),
]

map_impls = [
    PhysicalMap_LLM("gpt-4o"),
    PhysicalMap_LLM("gpt-4o-mini"),
]

# All combinations: 3 × 2 = 6 plans
all_plans = []
for filter_impl in filter_impls:
    for map_impl in map_impls:
        plan = PhysicalMap(
            map_impl,
            input=PhysicalFilter(filter_impl, input=data)
        )
        
        # Estimate cost considering both operators
        cost = estimate_plan_cost(plan, sample_data)
        quality = estimate_plan_quality(plan, sample_data)
        latency = estimate_plan_latency(plan, sample_data)
        
        all_plans.append((plan, cost, quality, latency))

# Select best plan
best = select_best_plan(all_plans, objective, constraints)
```

### Logical Optimizations

Abacus also applies traditional query optimization techniques:

```python
# Filter pushdown
def optimize_filter_pushdown(logical_plan):
    """
    Move filters as early as possible
    """
    if isinstance(logical_plan, LogicalJoin):
        left_filter = extract_filter_on_left(logical_plan.predicate)
        right_filter = extract_filter_on_right(logical_plan.predicate)
        
        if left_filter:
            logical_plan.left = LogicalFilter(
                logical_plan.left, 
                left_filter
            )
        
        if right_filter:
            logical_plan.right = LogicalFilter(
                logical_plan.right,
                right_filter
            )
    
    return logical_plan

# Join reordering
def optimize_join_order(logical_plan):
    """
    Reorder joins to minimize intermediate results
    """
    if has_multiple_joins(logical_plan):
        tables = extract_tables(logical_plan)
        predicates = extract_predicates(logical_plan)
        
        # Estimate cardinality after each join
        join_orders = enumerate_join_orders(tables)
        
        best_order = None
        best_cost = float('inf')
        
        for order in join_orders:
            estimated_cost = estimate_join_order_cost(order, predicates)
            if estimated_cost < best_cost:
                best_cost = estimated_cost
                best_order = order
        
        return construct_plan(best_order)
    
    return logical_plan
```

### Performance in SemBench

From the paper's results, Palimpzest with Abacus shows interesting characteristics:

**Movies Scenario (Table 4):**
- **Highest quality** on most queries (avg 0.73)
- More expensive than LOTUS (avg $0.82 vs $0.62)
- Q7 (complex join): Most expensive at $7.72 but good quality (0.68)

**E-Commerce Scenario (Table 5):**
- Supports 13/14 queries (missing Q14 due to no rank operator)
- Moderate cost (avg $0.42)
- Second-best quality (avg 0.70)

**MMQA Scenario (Table 7):**
- **Only system supporting all queries**
- Highest average quality (0.88)
- Most expensive (avg $1.62)
- Q7 (image-table join): $15.65 and 35 minutes!

**Trade-off pattern:** Palimpzest consistently chooses higher-quality, higher-cost plans. This reflects its optimization strategy of using more powerful models when quality is prioritized.

---

## Challenges and Future Directions

### Current Limitations

#### 1. **Accuracy of Cost Estimation**

**Problem:** Sample-based estimation can be inaccurate

```python
# Sample shows high selectivity
sample = [item1, item2, ..., item100]
filter_result = 90 out of 100 pass  # 90% selectivity

# But full data has different distribution
full_data_result = 1000 out of 10000 pass  # Only 10% selectivity!

# Cost estimate is way off:
estimated_cost = sample_cost × 100 = $50
actual_cost = $500  # 10× more expensive!
```

**Solutions being explored:**
- Better sampling strategies (stratified sampling)
- Progressive sampling (start small, sample more if needed)
- Learning from past queries on similar data

#### 2. **Quality-Cost Trade-off is Hard**

**Problem:** Quality metrics don't capture all aspects

```python
# Scenario: Extract product brands

# Model A output:
brands_A = ["Nike", "Adidas", "Puma", "Reebok"]
accuracy_A = 95%
cost_A = $5

# Model B output:
brands_B = ["Nike", "Adidas", "puma", "REEBOK"]  # Inconsistent casing
accuracy_B = 95%  # Same accuracy!
cost_B = $2

# Both have 95% accuracy, but A is more usable
# Simple accuracy metric doesn't capture this
```

**Solutions needed:**
- More sophisticated quality metrics
- Task-specific quality assessment
- User feedback loops

#### 3. **Optimization is Expensive**

**Problem:** Sampling and measuring itself costs money

```python
# To optimize a query with 5 operators, each with 4 physical impls:
# Need to evaluate 4^5 = 1024 plan combinations
# Even with sampling, that's expensive!

optimization_cost = 1024 plans × $0.10 per sample = $102.40
# Just to find the best plan!

# If actual query only costs $50, optimization isn't worth it
```

**Solutions:**
- Caching optimization results for similar queries
- Pruning unpromising plans early
- Learning which plans work well for which query patterns

#### 4. **Stochastic Operators**

**Problem:** LLM outputs vary between runs

```python
# Same query, same model, different results:

# Run 1
result_1 = semantic_filter(data, "positive sentiment")
count_1 = 847 items

# Run 2  
result_2 = semantic_filter(data, "positive sentiment")
count_2 = 831 items  # 16 items different!

# Which cost estimate is correct?
# What quality score should we report?
```

**Solutions:**
- Run operators multiple times and average
- Use temperature=0 when available
- Model variance in cost estimates

### Promising Research Directions

#### 1. **Learned Cost Models**

Instead of sampling every query, learn patterns:

```python
# Train a model to predict cost/quality/latency
# Based on query features

def predict_operator_cost(operator, data_stats):
    """
    Use ML model trained on past queries
    """
    features = extract_features(operator, data_stats)
    # Features: operator type, model, data size, data modality, etc.
    
    predicted_cost = cost_model.predict(features)
    predicted_quality = quality_model.predict(features)
    predicted_latency = latency_model.predict(features)
    
    return (predicted_cost, predicted_quality, predicted_latency)

# This avoids expensive sampling for every query
```

#### 2. **Operator Fusion**

Combine multiple semantic operators into one LLM call:

```python
# Original plan: Two separate operators
result = (
    df.filter(lambda x: AI.IF(x, "mentions sustainability"))
      .map(lambda x: AI.EXTRACT(x, "extract brand name"))
)

# Costs:
# Filter: 1000 items × $0.001 = $1.00
# Map: 300 items (after filter) × $0.001 = $0.30
# Total: $1.30

# Fused plan: Single operator
result = df.map(lambda x: AI.FUSED(
    x, 
    """
    If this mentions sustainability, extract the brand name.
    Otherwise return null.
    """
))

# Cost: 1000 items × $0.0012 = $1.20
# Savings: $0.10 (8% reduction)
# Plus: Only one round-trip to LLM (lower latency)
```

#### 3. **Incremental Optimization**

Refine plans as query executes:

```python
def adaptive_execution(logical_plan, objective):
    """
    Start with best-guess plan, improve over time
    """
    
    # Start with fast, cheap plan
    current_plan = get_quick_plan(logical_plan)
    
    results = []
    processed_items = 0
    
    for batch in data_batches:
        # Execute current plan on batch
        batch_result = current_plan.execute(batch)
        results.extend(batch_result)
        processed_items += len(batch)
        
        # Periodically re-optimize based on actual performance
        if processed_items % 1000 == 0:
            actual_cost = measure_cost_so_far()
            actual_quality = estimate_quality(results)
            
            # If not meeting objectives, try different plan
            if not meets_objectives(actual_cost, actual_quality, objective):
                current_plan = reoptimize(
                    logical_plan, 
                    actual_cost,
                    actual_quality,
                    objective
                )
    
    return results
```

#### 4. **Multi-Query Optimization**

Optimize multiple queries together:

```python
# User runs similar queries over time
query1 = df.filter("positive reviews")
query2 = df.filter("negative reviews")  
query3 = df.filter("neutral reviews")

# Naive: Run separately
# Cost: 3 × (1000 items × $0.001) = $3.00

# Optimized: Combine into single LLM call
query_combined = df.map("""
    Classify each review as positive, negative, or neutral
""")

# Then filter results for each query
# Cost: 1000 items × $0.0012 = $1.20
# Savings: 60%!

# Cache result for future queries
```

#### 5. **Approximate Operators with Guarantees**

Provide confidence bounds on approximate results:

```python
def approximate_filter_with_bounds(data, predicate, budget):
    """
    Return approximate result with confidence interval
    """
    
    # Stage 1: Cheap embedding filter
    candidates = embedding_filter(data, predicate, threshold=0.6)
    
    # Stage 2: Sample candidates and verify with LLM
    sample_size = budget / llm_cost_per_item
    sample = random.sample(candidates, int(sample_size))
    
    verified = llm_filter(sample, predicate)
    
    # Extrapolate with confidence bounds
    precision = len(verified) / len(sample)
    recall_estimate = 0.95  # From embedding filter properties
    
    # Statistical confidence interval
    lower_bound = precision - 1.96 × sqrt(precision × (1-precision) / len(sample))
    upper_bound = precision + 1.96 × sqrt(precision × (1-precision) / len(sample))
    
    estimated_result_count = len(candidates) × precision
    
    return {
        "estimate": estimated_result_count,
        "confidence_interval": (
            len(candidates) × lower_bound,
            len(candidates) × upper_bound
        ),
        "confidence_level": 0.95
    }

# Example output:
# {
#   "estimate": 427,
#   "confidence_interval": (398, 456),
#   "confidence_level": 0.95
# }
# "We're 95% confident the true count is between 398 and 456"
```

### Integration with Traditional Optimization

The future likely involves **hybrid systems** that optimize both traditional and semantic operators:

```sql
SELECT p.product_name, AVG(r.rating) as avg_rating
FROM products p
JOIN reviews r ON p.id = r.product_id
WHERE p.category = 'electronics'  -- Traditional filter
  AND AI.IF(r.review_text, 'mentions battery life')  -- Semantic filter
GROUP BY p.product_name
HAVING COUNT(*) > 10  -- Traditional having
ORDER BY AI.RANK(p.product_name, 'products most liked by tech enthusiasts')  -- Semantic rank
LIMIT 10;
```

**Optimization considerations:**
1. Push traditional filter (category) as early as possible
2. Consider join order: small filtered table first
3. Decide where to apply semantic filter: before or after join?
4. Use indexes for traditional operations
5. Use embeddings or LLMs for semantic operations
6. Balance cost across all operators

### The Grand Challenge

> **How do we build optimizers that can automatically navigate the complex trade-off space of cost, quality, and latency across both traditional and semantic operators, while adapting to different user priorities and learning from experience?**

This remains an open and active area of research!

---

## Conclusion

Cost-based query planning has evolved from optimizing disk I/O in the 1970s to optimizing LLM token consumption in 2025. The core principles remain:

1. **Enumerate alternatives:** There are many ways to execute a query
2. **Estimate costs:** Use models (statistical or sampled) to predict performance
3. **Choose optimally:** Select the plan that best meets objectives

But semantic operators introduce fundamental new challenges:
- Costs are 1000× higher than traditional operations
- Quality varies and must be explicitly optimized
- Plans are stochastic rather than deterministic
- The trade-off space is multi-dimensional

Systems like Palimpzest's Abacus optimizer represent the cutting edge of addressing these challenges, combining classical techniques (Cascades framework) with novel approaches (sampling-based measurement, multi-objective optimization).

The future of query optimization will likely involve:
- Learned cost models
- Adaptive execution strategies
- Operator fusion
- Approximate computing with guarantees
- Hybrid traditional-semantic optimization

As LLM capabilities grow and costs decrease, semantic query processing will become increasingly practical, and sophisticated optimization will be essential for making these systems efficient and cost-effective.
