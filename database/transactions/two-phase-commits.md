# Two-Phase Commit Protocol Guide

## Overview

Two-Phase Commit (2PC) is a distributed transaction protocol designed to ensure consistency across multiple systems. It's particularly useful in scenarios where multiple services need to agree on and complete a transaction atomically - meaning either all services complete their operations, or none do.

## Protocol Phases

### Phase 1 - Prepare
1. A coordinator (transaction manager) sends a prepare message to all participants
2. Each participant:
   - Validates if it can complete the transaction
   - Locks necessary resources
   - Writes prepare record to stable storage
   - Responds with "ready" or "abort"
3. If any participant responds "abort" or times out, the entire transaction is rolled back

### Phase 2 - Commit
1. If all participants responded "ready":
   - Coordinator writes commit decision to stable storage
   - Sends "commit" message to all participants
2. Each participant:
   - Completes their part of the transaction
   - Releases locked resources
   - Sends confirmation to coordinator
3. If any participant fails during commit:
   - Recovery procedures are initiated using stored prepare records

## Implementation Examples

### Python Implementation

```python
from enum import Enum
from typing import List, Dict

class TransactionState(Enum):
    INIT = "init"
    PREPARING = "preparing"
    READY = "ready"
    COMMITTING = "committing"
    COMMITTED = "committed"
    ABORTED = "aborted"

class Coordinator:
    def __init__(self):
        self.participants = []
        self.state = TransactionState.INIT
        
    def add_participant(self, participant):
        self.participants.append(participant)
    
    def execute_transaction(self, transaction_data: Dict) -> bool:
        # Phase 1: Prepare
        self.state = TransactionState.PREPARING
        for participant in self.participants:
            response = participant.prepare(transaction_data)
            if response != TransactionState.READY:
                self.rollback_all()
                return False
        
        # Phase 2: Commit
        self.state = TransactionState.COMMITTING
        for participant in self.participants:
            participant.commit(transaction_data)
        
        self.state = TransactionState.COMMITTED
        return True
    
    def rollback_all(self):
        self.state = TransactionState.ABORTED
        for participant in self.participants:
            participant.rollback()

class Participant:
    def __init__(self, name: str):
        self.name = name
        self.state = TransactionState.INIT
        self.locked_resources = []
    
    def prepare(self, transaction_data: Dict) -> TransactionState:
        self.state = TransactionState.PREPARING
        if self.can_complete_transaction(transaction_data):
            self.lock_resources()
            self.state = TransactionState.READY
            return TransactionState.READY
        return TransactionState.ABORTED
    
    def commit(self, transaction_data: Dict):
        self.state = TransactionState.COMMITTING
        self.complete_transaction(transaction_data)
        self.release_resources()
        self.state = TransactionState.COMMITTED
    
    def rollback(self):
        self.release_resources()
        self.state = TransactionState.ABORTED
    
    def can_complete_transaction(self, transaction_data: Dict) -> bool:
        # Implementation-specific validation logic
        return True
    
    def lock_resources(self):
        # Implementation-specific resource locking
        pass
    
    def release_resources(self):
        # Implementation-specific resource release
        self.locked_resources = []
    
    def complete_transaction(self, transaction_data: Dict):
        # Implementation-specific transaction logic
        pass
```

### Go Implementation

```go
package twophasecommit

import (
    "context"
    "errors"
    "sync"
)

type TransactionState string

const (
    StateInit       TransactionState = "init"
    StatePreparing  TransactionState = "preparing"
    StateReady      TransactionState = "ready"
    StateCommitting TransactionState = "committing"
    StateCommitted  TransactionState = "committed"
    StateAborted    TransactionState = "aborted"
)

type TransactionData map[string]interface{}

type Participant interface {
    Prepare(ctx context.Context, data TransactionData) error
    Commit(ctx context.Context, data TransactionData) error
    Rollback(ctx context.Context) error
}

type Coordinator struct {
    participants []Participant
    state       TransactionState
    mu          sync.Mutex
}

func NewCoordinator() *Coordinator {
    return &Coordinator{
        state: StateInit,
    }
}

func (c *Coordinator) AddParticipant(p Participant) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.participants = append(c.participants, p)
}

func (c *Coordinator) ExecuteTransaction(ctx context.Context, data TransactionData) error {
    c.mu.Lock()
    defer c.mu.Unlock()

    // Phase 1: Prepare
    c.state = StatePreparing
    for _, participant := range c.participants {
        if err := participant.Prepare(ctx, data); err != nil {
            c.rollbackAll(ctx)
            return err
        }
    }

    // Phase 2: Commit
    c.state = StateCommitting
    for _, participant := range c.participants {
        if err := participant.Commit(ctx, data); err != nil {
            // In a real implementation, you'd need more sophisticated error handling here
            return err
        }
    }

    c.state = StateCommitted
    return nil
}

func (c *Coordinator) rollbackAll(ctx context.Context) error {
    c.state = StateAborted
    var rollbackErr error
    for _, participant := range c.participants {
        if err := participant.Rollback(ctx); err != nil {
            rollbackErr = err
        }
    }
    return rollbackErr
}

// Example participant implementation
type ResourceParticipant struct {
    name            string
    state          TransactionState
    lockedResources []string
    mu             sync.Mutex
}

func NewResourceParticipant(name string) *ResourceParticipant {
    return &ResourceParticipant{
        name:  name,
        state: StateInit,
    }
}

func (p *ResourceParticipant) Prepare(ctx context.Context, data TransactionData) error {
    p.mu.Lock()
    defer p.mu.Unlock()

    p.state = StatePreparing
    if !p.canCompleteTransaction(data) {
        return errors.New("cannot complete transaction")
    }

    p.lockResources()
    p.state = StateReady
    return nil
}

func (p *ResourceParticipant) Commit(ctx context.Context, data TransactionData) error {
    p.mu.Lock()
    defer p.mu.Unlock()

    p.state = StateCommitting
    if err := p.completeTransaction(data); err != nil {
        return err
    }
    p.releaseResources()
    p.state = StateCommitted
    return nil
}

func (p *ResourceParticipant) Rollback(ctx context.Context) error {
    p.mu.Lock()
    defer p.mu.Unlock()

    p.releaseResources()
    p.state = StateAborted
    return nil
}

func (p *ResourceParticipant) canCompleteTransaction(data TransactionData) bool {
    // Implementation-specific validation logic
    return true
}

func (p *ResourceParticipant) lockResources() {
    // Implementation-specific resource locking
}

func (p *ResourceParticipant) releaseResources() {
    p.lockedResources = nil
}

func (p *ResourceParticipant) completeTransaction(data TransactionData) error {
    // Implementation-specific transaction logic
    return nil
}
```

## Advantages and Disadvantages

### Advantages
- Strong consistency guarantees across distributed systems
- Clear failure handling mechanisms
- Predictable and verifiable transaction outcomes
- Well-defined recovery procedures

### Disadvantages
- Blocking protocol (participants lock resources during the process)
- Performance overhead from network communication
- Coordinator becomes a single point of failure
- Timeout handling can be complex
- Not suitable for long-running transactions

## Modern Alternatives

In modern distributed systems, alternatives to 2PC are often preferred:
- Saga Pattern for long-running distributed transactions
- Eventual Consistency where absolute consistency isn't required
- Event-driven architectures with compensating transactions
- CRDTs (Conflict-free Replicated Data Types) for specific use cases

## Use Cases

Two-Phase Commit is particularly useful in:
- Financial transactions across multiple systems
- Inventory management across distributed warehouses
- Database operations spanning multiple shards
- Cross-service operations requiring strict consistency
