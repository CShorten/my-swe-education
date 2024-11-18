# Chapter 4: Networks of Queues: From Theory to Implementation

## 4.1 Introduction to Queueing Networks

Queueing networks connect multiple queues where customers flow between service stations. Examples include:
- Manufacturing assembly lines
- Computer networks
- Hospital patient flow
- Airport passenger systems

Let's implement a flexible queueing network simulator:

```python
from enum import Enum
from dataclasses import dataclass
import numpy as np
from typing import Dict, List, Optional, Tuple
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict

class NodeType(Enum):
    SOURCE = "source"
    QUEUE = "queue"
    SINK = "sink"

@dataclass
class Customer:
    id: int
    entry_time: float
    route: List[int] = None
    current_node: int = 0
    service_times: Dict[int, float] = None
    total_wait_time: float = 0.0

class QueueingNode:
    def __init__(self, 
                 node_id: int,
                 service_rate: float,
                 num_servers: int = 1,
                 node_type: NodeType = NodeType.QUEUE):
        self.id = node_id
        self.service_rate = service_rate
        self.num_servers = num_servers
        self.type = node_type
        
        # State variables
        self.queue = []
        self.servers = [None] * num_servers
        self.busy_servers = 0
        
        # Statistics
        self.total_arrivals = 0
        self.total_departures = 0
        self.total_wait_time = 0.0
        self.busy_time = 0.0
        self.queue_length_history = []

class QueueingNetwork:
    def __init__(self):
        self.nodes: Dict[int, QueueingNode] = {}
        self.routing_matrix: Dict[Tuple[int, int], float] = {}
        self.current_time = 0.0
        self.event_queue = []
        self.customers: Dict[int, Customer] = {}
        self.customer_counter = 0
        
    def add_node(self, 
                 node_id: int,
                 service_rate: float,
                 num_servers: int = 1,
                 node_type: NodeType = NodeType.QUEUE):
        """Add a node to the network"""
        self.nodes[node_id] = QueueingNode(
            node_id, service_rate, num_servers, node_type)
    
    def add_route(self, 
                 from_node: int,
                 to_node: int,
                 probability: float = 1.0):
        """Add routing probability between nodes"""
        self.routing_matrix[(from_node, to_node)] = probability
        
    def get_next_node(self, current_node: int) -> Optional[int]:
        """Determine next node based on routing probabilities"""
        possible_routes = [
            (to_node, prob) 
            for (from_node, to_node), prob in self.routing_matrix.items()
            if from_node == current_node
        ]
        
        if not possible_routes:
            return None
            
        nodes, probs = zip(*possible_routes)
        return np.random.choice(nodes, p=probs)
    
    def generate_service_time(self, node_id: int) -> float:
        """Generate service time for a node"""
        return np.random.exponential(1/self.nodes[node_id].service_rate)
    
    def schedule_event(self, event_time: float, event_type: str, 
                      customer_id: int, node_id: int):
        """Add event to priority queue"""
        heapq.heappush(
            self.event_queue,
            (event_time, event_type, customer_id, node_id)
        )
        
    def process_arrival(self, customer_id: int, node_id: int):
        """Process customer arrival at a node"""
        node = self.nodes[node_id]
        node.total_arrivals += 1
        
        if node.busy_servers < node.num_servers:
            # Assign to free server
            server_id = node.servers.index(None)
            node.servers[server_id] = customer_id
            node.busy_servers += 1
            
            # Schedule departure
            service_time = self.generate_service_time(node_id)
            departure_time = self.current_time + service_time
            self.schedule_event(
                departure_time, "departure", customer_id, node_id)
        else:
            # Add to queue
            node.queue.append(customer_id)
            
        # Record queue length
        node.queue_length_history.append(
            (self.current_time, len(node.queue)))
            
    def process_departure(self, customer_id: int, node_id: int):
        """Process customer departure from a node"""
        node = self.nodes[node_id]
        node.total_departures += 1
        
        # Find and free server
        server_id = node.servers.index(customer_id)
        node.servers[server_id] = None
        node.busy_servers -= 1
        
        # Process next customer in queue if any
        if node.queue:
            next_customer = node.queue.pop(0)
            node.servers[server_id] = next_customer
            node.busy_servers += 1
            
            service_time = self.generate_service_time(node_id)
            departure_time = self.current_time + service_time
            self.schedule_event(
                departure_time, "departure", next_customer, node_id)
        
        # Route customer to next node
        next_node = self.get_next_node(node_id)
        if next_node is not None:
            self.schedule_event(
                self.current_time, "arrival", customer_id, next_node)
```

## 4.2 Jackson Networks

Jackson networks are a special class of queueing networks where:
1. External arrivals are Poisson
2. Service times are exponential
3. Routing is probabilistic
4. Nodes are independent

Let's implement a Jackson network analyzer:

```python
class JacksonNetworkAnalyzer:
    def __init__(self, network: QueueingNetwork):
        self.network = network
        
    def calculate_arrival_rates(self) -> Dict[int, float]:
        """
        Calculate effective arrival rates using flow balance equations
        """
        n = len(self.network.nodes)
        
        # Create transition matrix
        P = np.zeros((n, n))
        for (i, j), prob in self.network.routing_matrix.items():
            P[i][j] = prob
            
        # Solve flow balance equations
        # λj = γj + Σi λi pij
        # where γj is external arrival rate
        # Linear algebra solution...
        return self._solve_flow_equations(P)
    
    def check_stability(self) -> Dict[int, bool]:
        """Check stability condition for each node"""
        arrival_rates = self.calculate_arrival_rates()
        
        stability = {}
        for node_id, node in self.network.nodes.items():
            if node.type == NodeType.QUEUE:
                rho = arrival_rates[node_id] / \
                      (node.service_rate * node.num_servers)
                stability[node_id] = rho < 1
                
        return stability
```

## 4.3 Network Performance Visualization

```python
class NetworkVisualizer:
    def __init__(self, network: QueueingNetwork):
        self.network = network
        
    def create_network_graph(self):
        """Create visual representation of network"""
        G = nx.DiGraph()
        
        # Add nodes
        for node_id, node in self.network.nodes.items():
            G.add_node(node_id, 
                      type=node.type.value,
                      servers=node.num_servers)
        
        # Add edges with routing probabilities
        for (from_node, to_node), prob in \
            self.network.routing_matrix.items():
            G.add_edge(from_node, to_node, 
                      probability=f"{prob:.2f}")
        
        return G
    
    def plot_network(self):
        """Visualize network structure"""
        G = self.create_network_graph()
        
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G)
        
        # Draw nodes
        node_colors = {
            'source': 'lightgreen',
            'queue': 'lightblue',
            'sink': 'lightcoral'
        }
        
        for node_type in node_colors:
            nodes = [n for n, attr in G.nodes(data=True)
                    if attr['type'] == node_type]
            nx.draw_networkx_nodes(G, pos, 
                                 nodelist=nodes,
                                 node_color=node_colors[node_type])
        
        # Draw edges with probabilities
        nx.draw_networkx_edges(G, pos)
        edge_labels = nx.get_edge_attributes(G, 'probability')
        nx.draw_networkx_edge_labels(G, pos, edge_labels)
        
        return plt
```

## 4.4 Practical Example: Manufacturing System

```python
def simulate_manufacturing_line():
    """
    Simulate a manufacturing line with:
    - Initial processing (2 stations)
    - Quality control
    - Rework loop
    - Final assembly
    """
    network = QueueingNetwork()
    
    # Add nodes
    network.add_node(0, 5.0, 2, NodeType.SOURCE)  # Source
    network.add_node(1, 4.0, 2)  # Initial processing 1
    network.add_node(2, 3.5, 2)  # Initial processing 2
    network.add_node(3, 6.0, 1)  # Quality control
    network.add_node(4, 4.0, 1)  # Rework
    network.add_node(5, 3.0, 3)  # Final assembly
    network.add_node(6, 0.0, 1, NodeType.SINK)  # Sink
    
    # Add routes
    network.add_route(0, 1, 1.0)      # Source to Initial 1
    network.add_route(1, 2, 1.0)      # Initial 1 to 2
    network.add_route(2, 3, 1.0)      # Initial 2 to QC
    network.add_route(3, 4, 0.2)      # QC to Rework (20%)
    network.add_route(3, 5, 0.8)      # QC to Final (80%)
    network.add_route(4, 3, 1.0)      # Rework to QC
    network.add_route(5, 6, 1.0)      # Final to Sink
    
    return network
```

## 4.5 Types of Queueing Networks

1. **Open Networks**
   - Customers can enter and leave
   - External arrivals and departures
   - Example: Hospital emergency department

2. **Closed Networks**
   - Fixed number of customers
   - No external arrivals/departures
   - Example: Computer memory management

3. **Mixed Networks**
   - Combination of open and closed
   - Example: Production system with fixtures

## 4.6 Advanced Topics

1. **BCMP Networks**
   - Multiple customer classes
   - General service distributions
   - Different queue disciplines

2. **G-Networks**
   - Negative customers
   - Triggers and signals
   - Neural network interpretation

## 4.8 Further Reading

- "Queueing Networks and Markov Chains" by Gunter Bolch
- "Computer Networks" by Andrew S. Tanenbaum
- "Performance Modeling of Communication Networks" by Phuoc Tran-Gia
