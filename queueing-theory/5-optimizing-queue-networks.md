# Chapter 5: Optimization of Queueing Networks

## 5.1 Introduction to Network Optimization

Network optimization involves balancing multiple objectives:
- Minimizing waiting times
- Maximizing throughput
- Minimizing costs
- Optimizing resource allocation

Let's build an optimization framework:

```python
from typing import Dict, List, Tuple, Callable
import numpy as np
from scipy.optimize import minimize
import pandas as pd
from dataclasses import dataclass

@dataclass
class OptimizationConfig:
    min_servers: int = 1
    max_servers: int = 10
    min_service_rate: float = 0.1
    max_service_rate: float = 10.0
    server_cost: float = 1000  # Cost per server
    waiting_cost: float = 10   # Cost per unit time waiting
    service_cost: float = 5    # Cost per unit service rate

class NetworkOptimizer:
    def __init__(self, network: QueueingNetwork, config: OptimizationConfig):
        self.network = network
        self.config = config
        self.current_solution = None
        
    def total_cost_function(self, params: np.ndarray) -> float:
        """
        Calculate total cost including:
        - Server costs
        - Waiting time costs
        - Service rate costs
        """
        num_nodes = len(self.network.nodes)
        servers = params[:num_nodes]
        service_rates = params[num_nodes:]
        
        # Server costs
        server_cost = np.sum(servers) * self.config.server_cost
        
        # Service rate costs
        service_cost = np.sum(service_rates) * self.config.service_cost
        
        # Waiting time costs (using M/M/c formulas)
        waiting_cost = self._calculate_waiting_cost(servers, service_rates)
        
        return server_cost + service_cost + waiting_cost
    
    def _calculate_waiting_cost(self, 
                              servers: np.ndarray, 
                              service_rates: np.ndarray) -> float:
        """Calculate total waiting cost across network"""
        total_cost = 0
        arrival_rates = self._calculate_arrival_rates()
        
        for node_id in self.network.nodes:
            if self.network.nodes[node_id].type == NodeType.QUEUE:
                λ = arrival_rates[node_id]
                μ = service_rates[node_id]
                c = int(servers[node_id])
                
                # M/M/c waiting time formula
                ρ = λ/(c*μ)
                if ρ >= 1:
                    return float('inf')  # Unstable system
                
                Wq = self._calculate_mm_c_waiting_time(λ, μ, c)
                total_cost += Wq * λ * self.config.waiting_cost
                
        return total_cost
    
    def optimize_network(self) -> Dict:
        """
        Find optimal number of servers and service rates
        """
        num_nodes = len(self.network.nodes)
        
        # Initial guess
        x0 = np.ones(2 * num_nodes)  # Servers and service rates
        
        # Bounds
        bounds = []
        for _ in range(num_nodes):
            bounds.append((self.config.min_servers, 
                         self.config.max_servers))  # Server bounds
        for _ in range(num_nodes):
            bounds.append((self.config.min_service_rate, 
                         self.config.max_service_rate))  # Rate bounds
            
        # Optimize
        result = minimize(
            self.total_cost_function,
            x0,
            bounds=bounds,
            method='SLSQP',
            constraints=self._get_constraints()
        )
        
        self.current_solution = self._parse_solution(result.x)
        return self.current_solution
```

## 5.2 Resource Allocation Strategies

### 5.2.1 Dynamic Server Allocation

```python
class DynamicServerAllocator:
    def __init__(self, network: QueueingNetwork):
        self.network = network
        self.thresholds = {}
        
    def set_threshold(self, 
                     node_id: int, 
                     low_threshold: int, 
                     high_threshold: int):
        """Set queue length thresholds for adding/removing servers"""
        self.thresholds[node_id] = {
            'low': low_threshold,
            'high': high_threshold
        }
        
    def adjust_servers(self, node_id: int, queue_length: int) -> int:
        """
        Determine optimal number of servers based on queue length
        Returns number of servers to add (positive) or remove (negative)
        """
        if node_id not in self.thresholds:
            return 0
            
        thresholds = self.thresholds[node_id]
        current_servers = self.network.nodes[node_id].num_servers
        
        if queue_length > thresholds['high']:
            return 1  # Add server
        elif queue_length < thresholds['low']:
            return -1  # Remove server
        return 0  # No change
```

### 5.2.2 Adaptive Service Rates

```python
class ServiceRateOptimizer:
    def __init__(self, network: QueueingNetwork):
        self.network = network
        self.min_rate = 0.1
        self.max_rate = 10.0
        
    def optimize_service_rates(self, 
                             arrival_rates: Dict[int, float]) -> Dict[int, float]:
        """
        Adjust service rates based on arrival rates and queue lengths
        """
        optimal_rates = {}
        
        for node_id, node in self.network.nodes.items():
            if node.type == NodeType.QUEUE:
                λ = arrival_rates[node_id]
                queue_length = len(node.queue)
                
                # Calculate optimal service rate
                optimal_rate = self._calculate_optimal_rate(
                    λ, queue_length, node.num_servers)
                
                # Apply bounds
                optimal_rates[node_id] = np.clip(
                    optimal_rate, self.min_rate, self.max_rate)
                
        return optimal_rates
```

## 5.3 Load Balancing

```python
class LoadBalancer:
    def __init__(self, network: QueueingNetwork):
        self.network = network
        
    def calculate_workload(self, node_id: int) -> float:
        """Calculate current workload of a node"""
        node = self.network.nodes[node_id]
        return (len(node.queue) + node.busy_servers) / node.num_servers
        
    def get_optimal_route(self, 
                         from_node: int, 
                         possible_nodes: List[int]) -> int:
        """
        Determine optimal routing based on current workloads
        """
        workloads = {
            node_id: self.calculate_workload(node_id)
            for node_id in possible_nodes
        }
        
        # Use softmin for probabilistic routing
        temperatures = np.array(list(workloads.values()))
        probabilities = self._softmin(temperatures)
        
        return np.random.choice(
            list(workloads.keys()),
            p=probabilities
        )
        
    def _softmin(self, x: np.ndarray, temperature: float = 1.0) -> np.ndarray:
        """Softmin function for smooth load balancing"""
        exp_x = np.exp(-x / temperature)
        return exp_x / np.sum(exp_x)
```

## 5.4 Cost-Based Optimization Example

```python
def optimize_call_center():
    """
    Optimize a call center with multiple service levels
    """
    # Create network
    network = QueueingNetwork()
    
    # Add nodes for different service types
    network.add_node(0, 5.0, 1, NodeType.SOURCE)     # Calls arrive
    network.add_node(1, 2.0, 5)  # General inquiries
    network.add_node(2, 3.0, 3)  # Technical support
    network.add_node(3, 4.0, 2)  # Account management
    network.add_node(4, 0.0, 1, NodeType.SINK)      # Calls complete
    
    # Configure optimization
    config = OptimizationConfig(
        min_servers=1,
        max_servers=10,
        server_cost=2000,    # Cost per agent
        waiting_cost=50,     # Cost per minute waiting
        service_cost=10      # Cost per unit service rate
    )
    
    # Optimize
    optimizer = NetworkOptimizer(network, config)
    solution = optimizer.optimize_network()
    
    return solution
```

## 5.5 Real-time Optimization

```python
class RealTimeOptimizer:
    def __init__(self, network: QueueingNetwork):
        self.network = network
        self.server_allocator = DynamicServerAllocator(network)
        self.rate_optimizer = ServiceRateOptimizer(network)
        self.load_balancer = LoadBalancer(network)
        
    def optimize_step(self, current_time: float):
        """
        Perform one step of real-time optimization
        """
        # Update arrival rate estimates
        arrival_rates = self._estimate_arrival_rates()
        
        # Optimize service rates
        optimal_rates = self.rate_optimizer.optimize_service_rates(
            arrival_rates)
        
        # Adjust server allocation
        for node_id in self.network.nodes:
            queue_length = len(self.network.nodes[node_id].queue)
            server_adjustment = self.server_allocator.adjust_servers(
                node_id, queue_length)
            
            if server_adjustment != 0:
                self._adjust_servers(node_id, server_adjustment)
                
        return {
            'arrival_rates': arrival_rates,
            'optimal_rates': optimal_rates,
            'server_adjustments': self._get_server_counts()
        }
```

## 5.6 Performance Metrics and Monitoring

```python
class NetworkMonitor:
    def __init__(self, network: QueueingNetwork):
        self.network = network
        self.metrics_history = defaultdict(list)
        
    def record_metrics(self, current_time: float):
        """Record current network performance metrics"""
        metrics = {
            'time': current_time,
            'queue_lengths': {},
            'utilization': {},
            'waiting_times': {},
            'throughput': {}
        }
        
        for node_id, node in self.network.nodes.items():
            if node.type == NodeType.QUEUE:
                metrics['queue_lengths'][node_id] = len(node.queue)
                metrics['utilization'][node_id] = \
                    node.busy_servers / node.num_servers
                
        self.metrics_history['metrics'].append(metrics)
```
