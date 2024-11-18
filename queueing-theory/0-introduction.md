# Queueing Theory: Fundamentals and Implementation
## Introduction

Queueing Theory is a mathematical study of waiting lines, or queues. It provides models to predict queue behavior and optimize service systems. This report covers fundamental concepts and provides Python implementations of key queueing models.

## Core Concepts

### 1. Kendall's Notation (A/B/C/K/N/D)
- A: Arrival process distribution
- B: Service time distribution
- C: Number of servers
- K: System capacity
- N: Population size
- D: Queue discipline

Common distributions:
- M: Markovian (exponential)
- D: Deterministic
- G: General

### 2. Key Performance Metrics
- λ: Arrival rate
- μ: Service rate
- ρ: System utilization (λ/μ)
- Lq: Average queue length
- Wq: Average waiting time
- Ls: Average system length
- Ws: Average system time

## Implementation Examples

### 1. M/M/1 Queue Simulator

```python
import numpy as np
from collections import deque
import random

class MM1Queue:
    def __init__(self, arrival_rate, service_rate):
        self.arrival_rate = arrival_rate
        self.service_rate = service_rate
        self.queue = deque()
        self.current_time = 0
        self.server_busy = False
        self.service_end_time = float('inf')
        
        # Statistics
        self.total_wait_time = 0
        self.customers_served = 0
        self.max_queue_length = 0
        
    def generate_interarrival_time(self):
        return np.random.exponential(1/self.arrival_rate)
    
    def generate_service_time(self):
        return np.random.exponential(1/self.service_rate)
    
    def simulate(self, simulation_time):
        next_arrival = self.generate_interarrival_time()
        
        while self.current_time < simulation_time:
            # Handle next event (either arrival or service completion)
            if next_arrival < self.service_end_time:
                # Process arrival
                self.current_time = next_arrival
                self.queue.append(self.current_time)
                next_arrival = self.current_time + self.generate_interarrival_time()
                
                if not self.server_busy:
                    self.server_busy = True
                    arrival_time = self.queue.popleft()
                    self.total_wait_time += self.current_time - arrival_time
                    self.service_end_time = self.current_time + self.generate_service_time()
                    
            else:
                # Process service completion
                self.current_time = self.service_end_time
                self.customers_served += 1
                
                if self.queue:
                    arrival_time = self.queue.popleft()
                    self.total_wait_time += self.current_time - arrival_time
                    self.service_end_time = self.current_time + self.generate_service_time()
                else:
                    self.server_busy = False
                    self.service_end_time = float('inf')
                    
            self.max_queue_length = max(self.max_queue_length, len(self.queue))
    
    def get_statistics(self):
        avg_wait_time = self.total_wait_time / self.customers_served if self.customers_served > 0 else 0
        return {
            'Average Wait Time': avg_wait_time,
            'Customers Served': self.customers_served,
            'Max Queue Length': self.max_queue_length,
            'Utilization': self.customers_served * self.service_rate / self.current_time
        }
```

### 2. Little's Law Calculator

```python
class LittlesLaw:
    @staticmethod
    def calculate_L(lambda_rate, W):
        """
        Calculate average number in system (L)
        L = λW
        """
        return lambda_rate * W
    
    @staticmethod
    def calculate_W(lambda_rate, L):
        """
        Calculate average time in system (W)
        W = L/λ
        """
        return L / lambda_rate
    
    @staticmethod
    def calculate_lambda(L, W):
        """
        Calculate arrival rate (λ)
        λ = L/W
        """
        return L / W
```

### 3. M/M/c Multi-Server Queue Performance Calculator

```python
import math

class MMcQueue:
    def __init__(self, arrival_rate, service_rate, servers):
        self.lambda_rate = arrival_rate
        self.mu = service_rate
        self.c = servers
        self.rho = arrival_rate / (service_rate * servers)
    
    def calculate_p0(self):
        """Calculate P0 - probability of empty system"""
        sum_term = sum([(self.lambda_rate/(self.mu))**n / math.factorial(n) 
                       for n in range(self.c)])
        last_term = (self.lambda_rate/(self.mu))**self.c / \
                   (math.factorial(self.c) * (1 - self.rho))
        return 1 / (sum_term + last_term)
    
    def calculate_lq(self):
        """Calculate Lq - average queue length"""
        p0 = self.calculate_p0()
        numerator = (self.lambda_rate/self.mu)**self.c * self.lambda_rate * self.mu
        denominator = math.factorial(self.c-1) * (self.c*self.mu - self.lambda_rate)**2
        return p0 * numerator / denominator
    
    def calculate_wq(self):
        """Calculate Wq - average waiting time in queue"""
        return self.calculate_lq() / self.lambda_rate
    
    def calculate_ls(self):
        """Calculate Ls - average number in system"""
        return self.calculate_lq() + self.lambda_rate/self.mu
    
    def calculate_ws(self):
        """Calculate Ws - average time in system"""
        return self.calculate_wq() + 1/self.mu
```

## Example Usage and Analysis

```python
# Example 1: Simulate M/M/1 Queue
queue = MM1Queue(arrival_rate=2, service_rate=3)
queue.simulate(simulation_time=1000)
print("M/M/1 Queue Statistics:", queue.get_statistics())

# Example 2: Apply Little's Law
ll = LittlesLaw()
L = ll.calculate_L(lambda_rate=2, W=0.5)
print(f"Average number in system: {L}")

# Example 3: Analyze M/M/c Queue
mmc = MMcQueue(arrival_rate=10, service_rate=4, servers=3)
print(f"Average queue length: {mmc.calculate_lq():.2f}")
print(f"Average waiting time: {mmc.calculate_wq():.2f}")
print(f"Average system length: {mmc.calculate_ls():.2f}")
print(f"Average system time: {mmc.calculate_ws():.2f}")
```

## Practical Applications

1. **Call Centers**: Using M/M/c models to determine optimal staffing levels
2. **Healthcare**: Managing patient wait times in emergency departments
3. **Manufacturing**: Optimizing production line efficiency
4. **Network Traffic**: Analyzing packet queues in network routing
5. **Retail**: Checkout counter optimization

## Conclusion

Queueing Theory provides powerful tools for analyzing and optimizing systems involving waiting lines. The Python implementations demonstrate how these concepts can be applied to real-world scenarios, helping organizations make data-driven decisions about resource allocation and system design.
