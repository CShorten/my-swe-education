# Chapter 3: Multi-Server Queues (M/M/c)

## 3.1 Introduction to Multi-Server Systems

In real-world scenarios, many queueing systems employ multiple servers:
- Bank tellers
- Supermarket checkout counters
- Call center operators
- Restaurant servers

```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
import numpy as np
import heapq
from enum import Enum
import pandas as pd

class EventType(Enum):
    ARRIVAL = "arrival"
    DEPARTURE = "departure"

@dataclass
class Event:
    time: float
    type: EventType
    customer_id: int
    server_id: Optional[int] = None

@dataclass
class Server:
    id: int
    busy: bool = False
    current_customer: Optional[int] = None
    total_busy_time: float = 0.0
    last_busy_start: float = 0.0

class MMcQueue:
    def __init__(self, arrival_rate: float, service_rate: float, num_servers: int):
        """
        Initialize M/M/c queue system
        
        Parameters:
        arrival_rate (λ): Average arrivals per time unit
        service_rate (μ): Average service rate per server
        num_servers (c): Number of parallel servers
        """
        self.arrival_rate = arrival_rate
        self.service_rate = service_rate
        self.num_servers = num_servers
        
        # System stability check
        self.rho = arrival_rate / (service_rate * num_servers)
        if self.rho >= 1:
            raise ValueError("System unstable: λ/(cμ) must be < 1")
        
        # Initialize servers
        self.servers = [Server(id=i) for i in range(num_servers)]
        
        # System state
        self.queue = []
        self.event_queue: List[Event] = []
        self.current_time = 0.0
        self.customers_served = 0
        self.total_wait_time = 0.0
        self.queue_length_history = []
        
    def generate_interarrival_time(self) -> float:
        return np.random.exponential(1/self.arrival_rate)
    
    def generate_service_time(self) -> float:
        return np.random.exponential(1/self.service_rate)
    
    def find_available_server(self) -> Optional[Server]:
        """Find first available server or return None if all busy"""
        for server in self.servers:
            if not server.busy:
                return server
        return None
    
    def schedule_event(self, event: Event):
        """Add event to priority queue"""
        heapq.heappush(self.event_queue, (event.time, event))
    
    def run_simulation(self, max_time: float) -> Dict:
        """
        Run simulation for specified time
        Returns performance metrics
        """
        # Schedule first arrival
        first_arrival = Event(
            time=self.generate_interarrival_time(),
            type=EventType.ARRIVAL,
            customer_id=0
        )
        self.schedule_event(first_arrival)
        
        while self.event_queue and self.current_time < max_time:
            # Process next event
            self.current_time, event = heapq.heappop(self.event_queue)
            
            if event.type == EventType.ARRIVAL:
                self.handle_arrival(event)
            else:
                self.handle_departure(event)
                
            # Record queue length
            self.queue_length_history.append(
                (self.current_time, len(self.queue))
            )
            
        return self.calculate_metrics()
    
    def handle_arrival(self, event: Event):
        """Process customer arrival"""
        server = self.find_available_server()
        
        if server:
            # Start service immediately
            server.busy = True
            server.current_customer = event.customer_id
            server.last_busy_start = self.current_time
            
            # Schedule departure
            departure_time = self.current_time + self.generate_service_time()
            departure = Event(
                time=departure_time,
                type=EventType.DEPARTURE,
                customer_id=event.customer_id,
                server_id=server.id
            )
            self.schedule_event(departure)
        else:
            # All servers busy, join queue
            self.queue.append(event.customer_id)
        
        # Schedule next arrival
        next_arrival = Event(
            time=self.current_time + self.generate_interarrival_time(),
            type=EventType.ARRIVAL,
            customer_id=event.customer_id + 1
        )
        self.schedule_event(next_arrival)
    
    def handle_departure(self, event: Event):
        """Process customer departure"""
        server = self.servers[event.server_id]
        
        # Update server statistics
        server.total_busy_time += self.current_time - server.last_busy_start
        self.customers_served += 1
        
        if self.queue:
            # Start service for next customer in queue
            next_customer = self.queue.pop(0)
            server.current_customer = next_customer
            server.last_busy_start = self.current_time
            
            # Schedule departure
            departure_time = self.current_time + self.generate_service_time()
            departure = Event(
                time=departure_time,
                type=EventType.DEPARTURE,
                customer_id=next_customer,
                server_id=server.id
            )
            self.schedule_event(departure)
        else:
            # No customers waiting, server becomes idle
            server.busy = False
            server.current_customer = None
```

## 3.2 Key Performance Metrics for M/M/c Queues

```python
def calculate_mmc_metrics(self) -> Dict:
    """Calculate theoretical M/M/c metrics"""
    λ = self.arrival_rate
    μ = self.service_rate
    c = self.num_servers
    ρ = λ/(c*μ)
    
    # Calculate P0 (probability of empty system)
    sum_term = sum([(c*ρ)**n/np.math.factorial(n) for n in range(c)])
    last_term = (c*ρ)**c/(np.math.factorial(c)*(1-ρ))
    P0 = 1/(sum_term + last_term)
    
    # Calculate performance metrics
    Lq = P0 * (λ/μ)**c * ρ/(np.math.factorial(c)*(1-ρ)**2)
    L = Lq + λ/μ
    Wq = Lq/λ
    W = Wq + 1/μ
    
    return {
        'P0': P0,          # Probability of empty system
        'Lq': Lq,          # Average queue length
        'L': L,            # Average system length
        'Wq': Wq,          # Average waiting time
        'W': W,            # Average system time
        'utilization': ρ   # Server utilization
    }
```

## 3.3 Visualizing Multi-Server Performance

```python
class MMcVisualizer:
    def __init__(self, queue: MMcQueue):
        self.queue = queue
        
    def plot_server_utilization(self):
        """Plot utilization of each server"""
        utilizations = [
            s.total_busy_time/self.queue.current_time 
            for s in self.queue.servers
        ]
        
        plt.figure(figsize=(10, 6))
        plt.bar(range(len(utilizations)), utilizations)
        plt.axhline(y=self.queue.rho, color='r', linestyle='--', 
                   label='Theoretical')
        plt.xlabel('Server ID')
        plt.ylabel('Utilization')
        plt.title('Server Utilization')
        plt.legend()
        return plt
    
    def animate_queue_evolution(self):
        """Create animation of queue and server states"""
        # Implementation of queue animation
        pass
```

## 3.4 Practical Example: Airport Security Checkpoints

```python
def simulate_airport_security():
    # Parameters
    arrival_rate = 120  # passengers per hour
    service_rate = 45   # passengers per hour per checkpoint
    num_checkpoints = 3
    simulation_time = 8  # hours
    
    # Create and run simulation
    security = MMcQueue(
        arrival_rate=arrival_rate/60,  # convert to per minute
        service_rate=service_rate/60,
        num_servers=num_checkpoints
    )
    
    metrics = security.run_simulation(simulation_time * 60)
    
    # Analyze results
    visualizer = MMcVisualizer(security)
    visualizer.plot_server_utilization()
    
    return metrics
```

## 3.5 Comparing M/M/1 vs M/M/c

Key differences:
1. System stability condition: λ < cμ
2. More complex P0 calculation
3. Different queue length distribution
4. Resource allocation considerations

## 3.7 Further Reading

- "Queueing Networks and Markov Chains" by Gunter Bolch
- "Performance Analysis of Computer Networks" by Jeremiah F. Hayes
