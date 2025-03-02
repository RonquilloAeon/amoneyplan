# Money Plan App

A personal cashflow tracker built with event sourcing that helps you manage your finances when you get paid. This app records every money movement as an immutable event, enabling you to replay history, audit your cashflow, and answer questions like “How much did I save in Wealthfront last year?”

> **Note:**  
> This project is an evolution of my long-time "Money Plan" concept—a spin on envelope (zero-based) budgeting. While my old spreadsheet worked well for day-to-day budgeting, it lacked a robust history and audit trail. This app leverages event sourcing (using the [eventsourcing](https://github.com/johnbywater/eventsourcing) library) to provide full traceability of every fund movement.

## Overview

- **Purpose:**  
  When you get paid, you create a new Money Plan by recording your initial checking account balance (e.g. Ally Checking) and then allocating funds into one or more Accounts.  
  - **Accounts & Buckets:**  
    - Each **Account** is a shared global entity (e.g. “Wealthfront”, “Apple Card”) that can be used across multiple plans for historical analysis.  
    - An Account is subdivided into one or more **Buckets** (or sub-accounts) that further categorize your funds (e.g. “General Savings”, “House Savings”).  
  - **Editing vs. Commitment:**  
    - A plan may be worked on without any accounts during editing.
    - However, before a plan is committed, it must have at least one account. Additionally, each account must contain at least one bucket. If an account is created without specifying buckets, a default bucket named **"Default"** is automatically added.
  - **Invariant at Commit:**  
    When the plan is committed, the sum of all bucket allocations across all accounts must equal the initial balance.
  - **Notes:**  
    Each plan includes a free-text notes field for additional context.

- **Why Event Sourcing?**  
  - **Complete History & Audit:** Every allocation, adjustment, and configuration change is recorded as an immutable event.
  - **Reversibility:** Corrections and reallocations are handled via compensating events, preserving a full audit trail.
  - **Learning Opportunity:** Experiment with key event sourcing patterns (event replay, snapshots, versioning) using the eventsourcing_django library.

---

## Domain Model

### MoneyPlan Aggregate

- **Attributes:**
  - `initialBalance: float` – The starting balance from your deposit.
  - `accounts: List[PlanAccountAllocation]` – A list of allocations into accounts for this plan.
  - `notes: str` – Free-text field for additional context.
  - `committed: bool` – Indicates whether the plan has been finalized.
- **Invariant (upon commit):**
  - The plan must have at least one account.
  - Each account must have at least one bucket.
  - The total of all bucket allocations (across all accounts) must equal `initialBalance`.

### Account & Plan Account Allocation

- **Account:**
  - Represents a shared financial entity (e.g. “Wealthfront”, “Apple Card”) that persists across plans.
- **PlanAccountAllocation:**
  - In a Money Plan, an account allocation references an account and its specific bucket allocations for that plan.
  - Each allocation includes one or more **Buckets**:
    - **Bucket:**
      - `bucketName: str`
      - `category: str` (e.g. “General Savings”, “House Savings”)
      - `allocatedAmount: float`
  - **Default Bucket:**  
    If no buckets are provided when an account is added, a default bucket named **"Default"** is automatically created.

---

## Domain Events

All events are defined as immutable records (using the eventsourcing_django library):

1. **PlanStarted**
   - **Fields:**
     - `initialBalance: float`
     - `defaultAllocations: List[AccountAllocationConfig]`  
       *Each configuration includes an account ID, account name, and a list of BucketConfigs (bucket name, category, and initial allocated amount).*
     - `notes: str`
     - `timestamp: datetime`
   - **Purpose:**  
     Begins a new Money Plan by setting the initial balance, notes, and default account allocation structure. If no allocation is provided, the plan can default to the previous plan’s configuration.

2. **BucketFundsAllocated**
   - **Fields:**
     - `accountId: str`
     - `bucketName: str`
     - `amount: float`
     - `timestamp: datetime`
   - **Purpose:**  
     Records the allocation of funds from the main balance into a specific bucket within an account.

3. **BucketAllocationReversed**
   - **Fields:**
     - `accountId: str`
     - `bucketName: str`
     - `previousAmount: float`
     - `correctedAmount: float`
     - `timestamp: datetime`
   - **Purpose:**  
     Corrects a previous allocation error by reversing the original amount and applying the corrected allocation.

4. **PlanBalanceAdjusted**
   - **Fields:**
     - `adjustment: float`
     - `reason: str`
     - `timestamp: datetime`
   - **Purpose:**  
     Adjusts the overall Money Plan balance (to fix errors or reflect manual corrections).

5. **AccountConfigurationChanged**
   - **Fields:**
     - `accountId: str`
     - `newBucketConfig: List[BucketConfig]`  
       *Each BucketConfig includes bucket name, category, and an optional initial allocation.*
     - `timestamp: datetime`
   - **Purpose:**  
     Updates the bucket configuration for a specific account in the current plan. This event changes the structure only; fund adjustments must be made via allocation events.

6. **PlanCommitted**
   - **Fields:**
     - `timestamp: datetime`
   - **Purpose:**  
     Finalizes the Money Plan. At commit time, the plan must have at least one account (and each account must have at least one bucket), and the sum of all bucket allocations must equal the initial balance.

## State Rehydration (Event Folding)

Implement an **evolve** function that processes events sequentially to rebuild the Money Plan state:

1. **PlanStarted:**  
   - Set `initialBalance`, `notes`, and mark `committed` as `false`.
   - Initialize accounts based on `defaultAllocations`. For each account, if no buckets are provided, add a default bucket named **"Default"**.

2. **BucketFundsAllocated:**  
   - Subtract the allocated amount from the main balance.
   - Increase the specified bucket’s allocated amount within the appropriate account.

3. **BucketAllocationAdjusted:**  
   - Modify the previous allocation by adding back the `PreviousAmount` and reducing the bucket’s balance.
   - Then apply the corrected allocation by subtracting the `correctedAmount` from the main balance and increasing the bucket’s balance.

4. **PlanBalanceAdjusted:**  
   - Modify the main balance by the adjustment amount.

5. **AccountConfigurationChanged:**  
   - Update the specified account’s bucket configuration. For new buckets added, initialize their allocated amounts to 0 if not provided.

6. **PlanCommitted:**  
   - Mark the plan as committed.
   - Validate that:
     - At least one account exists.
     - Each account has at least one bucket.
     - The sum of all bucket allocations equals the `initialBalance`.

## GraphQL API (Using Strawberry)

### GraphQL Types

1. **Bucket Type**
```python
@strawberry.type
class Bucket:
    bucketName: str
    category: str
    allocatedAmount: float
```

2.	**Account Type**
```python
@strawberry.type
class Account:
    accountId: str
    accountName: str
    buckets: List[Bucket]
```

3.	MoneyPlan Type
```python
@strawberry.type
class MoneyPlan:
    initialBalance: float
    notes: str
    accounts: List[Account]
    committed: bool
```

### Input Types
- PlanStartInput
```python
@strawberry.input
class PlanStartInput:
    initialBalance: float
    notes: str
    defaultAllocations: Optional[List["AccountAllocationConfigInput"]] = None
```

- AccountAllocationConfigInput
```python
@strawberry.input
class AccountAllocationConfigInput:
    accountId: str
    accountName: str
    buckets: List["BucketConfigInput"]
```

- BucketConfigInput
```python
@strawberry.input
class BucketConfigInput:
    bucketName: str
    category: str
    allocatedAmount: Optional[float] = 0.0
```

- AllocateFundsInput
```python
@strawberry.input
class AllocateFundsInput:
    accountId: str
    bucketName: str
    amount: float
```

- AdjustAllocationInput
```python
@strawberry.input
class AdjustAllocationInput:
    accountId: str
    bucketName: str
    previousAmount: float
    correctedAmount: float
```

- PlanBalanceAdjustInput
```python
@strawberry.input
class PlanBalanceAdjustInput:
    adjustment: float
    reason: str
```

- AccountConfigurationChangeInput
```python
@strawberry.input
class AccountConfigurationChangeInput:
    accountId: str
    newBucketConfig: List[BucketConfigInput]
```

### GraphQL Operations

**Queries**
- **moneyPlan**: Returns the current Money Plan state by loading and folding the event stream:
```python
@strawberry.type
class Query:
    @strawberry.field
    def money_plan(self) -> MoneyPlan:
        # Retrieve events via the eventsourcing_django library,
        # fold them to compute the current Money Plan state,
        # and return it.
        pass
```

**Mutations**
- startPlan
```python
@strawberry.mutation
def start_plan(self, input: PlanStartInput) -> MoneyPlan:
    # If defaultAllocations is not provided, use the previous plan’s configuration (if available).
    # Persist a PlanStarted event.
    # Rehydrate and return the updated Money Plan state.
    pass
```

- allocateFunds
```python
@strawberry.mutation
def allocate_funds(self, input: AllocateFundsInput) -> MoneyPlan:
    # Persist a BucketFundsAllocated event.
    # Recompute and return the updated Money Plan state.
    pass
```

- adjustAllocation
```python
@strawberry.mutation
def adjust_allocation(self, input: AdjustAllocationInput) -> MoneyPlan:
    # Persist a BucketAllocationAdjusted event.
    # Recompute and return the updated Money Plan state.
    pass
```

- adjustPlanBalance
```python
@strawberry.mutation
def adjust_plan_balance(self, input: PlanBalanceAdjustInput) -> MoneyPlan:
    # Persist a PlanBalanceAdjusted event.
    # Recompute and return updated state.
    pass
```

- changeAccountConfiguration
```python
@strawberry.mutation
def change_account_configuration(self, input: AccountConfigurationChangeInput) -> MoneyPlan:
    # Persist an AccountConfigurationChanged event.
    # Recompute and return updated state.
    pass
```

- commitPlan
```python
@strawberry.mutation
def commit_plan(self) -> MoneyPlan:
    # Persist a PlanCommitted event.
    # Validate that the plan contains at least one account,
    # each account has at least one bucket, and that the total of all bucket allocations equals the initialBalance.
    # If valid, mark the plan as committed and return the state; otherwise, reject the commit.
    pass
```


## Persistence & Integration with the Eventsourcing Library
- Event Store:
    - Use PostgreSQL (or another supported backend) in combination with the eventsourcing_django library to persist events.
- Snapshots:
    - Optionally implement snapshots to speed up state rehydration.
- Aggregate Implementation:
  - Implement a MoneyPlanAggregate class (using the eventsourcing_django library) with methods decorated with @event to record:
      - `start_plan(initial_balance, default_allocations, notes)`
      - `allocate_funds(account_id, bucket_name, amount)`
      - `reverse_allocation(account_id, bucket_name, original_amount, corrected_amount)`
      - `adjust_plan_balance(adjustment, reason)`
      - `change_account_configuration(account_id, new_bucket_config)`
      - `commit_plan()`
- The commit_plan method must enforce that:
    - The plan has at least one account.
    - Each account has at least one bucket.
    - The total of all bucket allocations equals the initialBalance.

## Business Rules & Invariants
- New Plans:
  - A calendar day may only have one plan
  - If there's an existing MoneyPlan, it must be committed before starting a new plan
- Editing vs. Commitment:
  - A Money Plan may be worked on without any accounts during editing.
  - However, before a plan is committed, it must have at least one account with at least one bucket.
- Default Bucket:
  - Each account requires at least one bucket. If none are provided, a default bucket named “Default” is added automatically.
- Invariant at Commit:
  - When a plan is committed, the sum of all bucket allocations (across all accounts) must equal the initial balance.
- Shared Accounts:
  - Accounts are shared across plans to allow querying historical fund allocations (e.g. “How much did I save in Wealthfront last year?”).

## Summary

The Money Plan app is an event-sourced personal cashflow tracker that:
- Starts with an initial balance and notes, and allows you to dynamically configure fund allocations.
- Works in Progress:
    - While editing, a plan can have no accounts.
    - Before committing, the plan must contain at least one account (and each account must have at least one bucket).
- Records every change via immutable events:
  - PlanStarted: Initializes the plan.
  - BucketFundsAllocated: Logs fund allocations to buckets.
  - BucketAllocationAdjusted: Handles corrections.
  - PlanBalanceAdjusted: Applies overall balance adjustments.
  - AccountConfigurationChanged: Updates account bucket configurations.
  - PlanCommitted: Finalizes the plan, enforcing that bucket totals equal the initial balance.
- Exposes a GraphQL API (via Strawberry) for querying and managing Money Plans.
- Uses the eventsourcing_django library to persist events, replay them to rehydrate state, and optionally implement snapshots.
- Supports shared accounts, so you can later analyze historical allocations (e.g. “How much did I save in Wealthfront last year?”).

## Django with MongoDB and PostgreSQL

- **MongoDB Integration:**  
  Although Django doesn’t natively support MongoDB, you can integrate it using third-party libraries such as [Djongo](https://www.djongo.org/) or [MongoEngine](https://mongoengine.org/).



## Dev Environment Setup

### Tools and Dependencies

- **Python Environment:**  
  - Use [Poetry](https://python-poetry.org/) for dependency management and packaging.
  - Use [Nox](https://nox.thea.codes/) to automate testing and linting.

- **Pre-commit Hooks:**  
  - Set up a `.pre-commit-config.yaml` with [Ruff](https://github.com/charliermarsh/ruff) for linting and code formatting.

### Local Development with Docker Compose

Create a `docker-compose.yml` file to run the Django app and database containers locally.
