# Chapter 2: The M/M/1 Queue: Theory and Implementation

## 2.1 What is an M/M/1 Queue?

The M/M/1 queue is the simplest yet most fundamental queueing system:
- First M: Markovian (exponential) arrival process
- Second M: Markovian (exponential) service times
- 1: Single server

Let's implement a comprehensive M/M/1 queue simulator:

```python
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Optional
import matplotlib.pyplot as plt
from collections import deque

@dataclass
class Customer:
    id: int
    arrival_time: float
    service_time: float
    service_start: Optional[float] = None
    departure_time: Optional[float] = None

class MM1Queue:
    def __init__(self, arrival_rate: float, service_rate: float):
        """
        Initialize M/M/1 queue
        
        Parameters:
        arrival_rate (λ): Average number of arrivals per time unit
        service_rate (μ): Average number of customers served per time unit
        """
        self.arrival_rate = arrival_rate
        self.service_rate = service_rate
        self.utilization = arrival_rate / service_rate
        
        # Validation
        if self.utilization >= 1:
            raise ValueError("System unstable: arrival rate must be less than service rate")
        
        # Queue state
        self.queue = deque()
        self.current_time = 0
        self.server_busy = False
        self.customers_served = []
        self.current_customer: Optional[Customer] = None
        
        # Performance metrics
        self.waiting_times = []
        self.queue_lengths = []
        self.system_times = []
    
    def generate_interarrival_time(self) -> float:
        return np.random.exponential(1/self.arrival_rate)
    
    def generate_service_time(self) -> float:
        return np.random.exponential(1/self.service_rate)
    
    def run_simulation(self, max_customers: int = 1000) -> Dict:
        """
        Run the queue simulation for a specified number of customers
        """
        customer_count = 0
        next_arrival_time = self.generate_interarrival_time()
        next_departure_time = float('inf')
        
        while customer_count < max_customers:
            # Determine next event
            if next_arrival_time < next_departure_time:
                # Process arrival
                self.current_time = next_arrival_time
                customer = Customer(
                    id=customer_count,
                    arrival_time=self.current_time,
                    service_time=self.generate_service_time()
                )
                
                if not self.server_busy:
                    # Server is free, begin service immediately
                    self.server_busy = True
                    customer.service_start = self.current_time
                    next_departure_time = self.current_time + customer.service_time
                    self.current_customer = customer
                else:
                    # Server is busy, join queue
                    self.queue.append(customer)
                
                # Schedule next arrival
                next_arrival_time = self.current_time + self.generate_interarrival_time()
                customer_count += 1
                
            else:
                # Process departure
                self.current_time = next_departure_time
                if self.current_customer:
                    self.current_customer.departure_time = self.current_time
                    self.customers_served.append(self.current_customer)
                
                if self.queue:
                    # Begin service for next customer in queue
                    next_customer = self.queue.popleft()
                    next_customer.service_start = self.current_time
                    next_departure_time = self.current_time + next_customer.service_time
                    self.current_customer = next_customer
                else:
                    # No customers in queue
                    self.server_busy = False
                    next_departure_time = float('inf')
                    self.current_customer = None
            
            # Record metrics
            self.queue_lengths.append((self.current_time, len(self.queue)))
            
        return self.calculate_metrics()
    
    def calculate_metrics(self) -> Dict:
        """Calculate key performance metrics"""
        df = pd.DataFrame([
            {
                'arrival_time': c.arrival_time,
                'service_start': c.service_start,
                'departure_time': c.departure_time,
                'waiting_time': c.service_start - c.arrival_time,
                'service_time': c.departure_time - c.service_start,
                'system_time': c.departure_time - c.arrival_time
            }
            for c in self.customers_served
        ])
        
        return {
            'average_waiting_time': df['waiting_time'].mean(),
            'average_system_time': df['system_time'].mean(),
            'average_queue_length': np.mean([ql for _, ql in self.queue_lengths]),
            'utilization': df['service_time'].sum() / self.current_time,
            'theoretical_metrics': self.get_theoretical_metrics()
        }
    
    def get_theoretical_metrics(self) -> Dict:
        """Calculate theoretical M/M/1 metrics"""
        ρ = self.arrival_rate / self.service_rate
        return {
            'utilization': ρ,
            'avg_queue_length': ρ**2 / (1 - ρ),
            'avg_system_length': ρ / (1 - ρ),
            'avg_waiting_time': ρ / (self.service_rate * (1 - ρ)),
            'avg_system_time': 1 / (self.service_rate * (1 - ρ))
        }
    
    def visualize_queue_evolution(self):
        """Create visualization of queue length over time"""
        times, lengths = zip(*self.queue_lengths)
        
        plt.figure(figsize=(12, 6))
        plt.step(times, lengths, where='post')
        plt.title('Queue Length Evolution Over Time')
        plt.xlabel('Time')
        plt.ylabel('Queue Length')
        plt.grid(True, alpha=0.3)
        return plt
```

## 2.2 Analyzing M/M/1 Queue Performance

Let's create a class to analyze and visualize queue performance:

```python
class MM1Analyzer:
    def __init__(self, queue: MM1Queue):
        self.queue = queue
        self.metrics = None
    
    def run_analysis(self, num_customers: int = 1000):
        """Run simulation and analyze results"""
        self.metrics = self.queue.run_simulation(num_customers)
        
        # Compare simulated vs theoretical results
        sim = self.metrics
        theory = sim['theoretical_metrics']
        
        comparison = pd.DataFrame({
            'Metric': ['Utilization', 'Avg Queue Length', 'Avg Waiting Time'],
            'Simulated': [
                sim['utilization'],
                sim['average_queue_length'],
                sim['average_waiting_time']
            ],
            'Theoretical': [
                theory['utilization'],
                theory['avg_queue_length'],
                theory['avg_waiting_time']
            ]
        })
        
        return comparison
    
    def visualize_waiting_time_distribution(self):
        """Plot distribution of waiting times"""
        waiting_times = [c.service_start - c.arrival_time 
                        for c in self.queue.customers_served]
        
        plt.figure(figsize=(10, 6))
        plt.hist(waiting_times, bins=30, density=True, alpha=0.7)
        
        # Plot theoretical exponential distribution
        x = np.linspace(0, max(waiting_times), 100)
        theory = self.metrics['theoretical_metrics']
        mean_wait = theory['avg_waiting_time']
        y = (1/mean_wait) * np.exp(-x/mean_wait)
        plt.plot(x, y, 'r-', lw=2, label='Theoretical')
        
        plt.title('Distribution of Waiting Times')
        plt.xlabel('Waiting Time')
        plt.ylabel('Density')
        plt.legend()
        return plt
```

## 2.3 Practical Example: Coffee Shop Queue

Let's model a coffee shop as an M/M/1 queue:

```python
def simulate_coffee_shop():
    # Average arrival rate: 30 customers per hour
    # Average service rate: 40 customers per hour
    queue = MM1Queue(arrival_rate=30/60, service_rate=40/60)
    analyzer = MM1Analyzer(queue)
    
    # Run simulation for 100 customers
    results = analyzer.run_analysis(100)
    print("\nCoffee Shop Queue Analysis:")
    print(results)
    
    # Visualize queue evolution
    queue.visualize_queue_evolution()
    plt.title('Coffee Shop Queue Length Over Time')
    
    # Visualize waiting times
    analyzer.visualize_waiting_time_distribution()
    plt.title('Coffee Shop Customer Waiting Times')
    
    return results

if __name__ == "__main__":
    simulate_coffee_shop()
```

## 2.4 Key Theoretical Results

For an M/M/1 queue with arrival rate λ and service rate μ:

1. **Stability Condition**: λ < μ
2. **Utilization**: ρ = λ/μ
3. **Average Queue Length**: Lq = ρ²/(1-ρ)
4. **Average System Length**: L = ρ/(1-ρ)
5. **Average Waiting Time**: Wq = ρ/(μ(1-ρ))
6. **Average System Time**: W = 1/(μ(1-ρ))

## 2.6 Further Reading

- "Queueing Systems, Volume 1: Theory" by Leonard Kleinrock
- "Performance Modeling and Design of Computer Systems" by Mor Harchol-Balter
