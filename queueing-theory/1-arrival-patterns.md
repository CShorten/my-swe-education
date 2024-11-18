# Chapter 1: Understanding Arrival Patterns and Interarrival Times

## 1.1 What Are Interarrival Times?

Interarrival time is the time between consecutive arrivals in a queue. Think of a coffee shop:
- Customer A arrives at 9:00 AM
- Customer B arrives at 9:03 AM
- Customer C arrives at 9:08 AM

The interarrival times would be:
- Between A and B: 3 minutes
- Between B and C: 5 minutes

Let's implement this concept in Python with clear visualizations:

```python
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict
from datetime import datetime, timedelta

class InterarrivalVisualizer:
    def __init__(self):
        self.arrivals = []
        self.interarrivals = []
        
    def simulate_customer_arrivals(self, 
                                 num_customers: int, 
                                 avg_arrival_rate: float) -> Dict:
        """
        Simulate customer arrivals and calculate interarrival times
        
        Parameters:
        num_customers: Number of customers to simulate
        avg_arrival_rate: Average number of customers per hour
        
        Returns:
        Dictionary containing arrival times and interarrival times
        """
        # Generate random interarrival times (exponentially distributed)
        interarrival_times = np.random.exponential(
            scale=60/avg_arrival_rate,  # Convert rate to minutes
            size=num_customers-1
        )
        
        # Calculate arrival times
        current_time = 0
        arrival_times = [current_time]
        
        for time in interarrival_times:
            current_time += time
            arrival_times.append(current_time)
            
        return {
            'arrival_times': arrival_times,
            'interarrival_times': interarrival_times
        }
    
    def visualize_arrivals_and_interarrivals(self, 
                                           data: Dict, 
                                           title: str = "Coffee Shop Example"):
        """
        Create a two-panel visualization showing:
        1. Customer arrival timeline
        2. Histogram of interarrival times
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # Plot 1: Timeline of arrivals
        ax1.eventplot(data['arrival_times'], lineoffsets=0.5, 
                     linelengths=0.5, color='blue')
        ax1.set_title('Customer Arrival Timeline')
        ax1.set_xlabel('Time (minutes)')
        ax1.set_ylabel('Arrivals')
        
        # Add annotations for first few interarrival times
        for i in range(min(3, len(data['arrival_times'])-1)):
            t1 = data['arrival_times'][i]
            t2 = data['arrival_times'][i+1]
            interarrival = t2 - t1
            
            # Add arrow and label
            mid_point = (t1 + t2) / 2
            ax1.annotate(
                f'{interarrival:.1f} min',
                xy=(mid_point, 0.5),
                xytext=(mid_point, 1),
                arrowprops=dict(arrowstyle='<->'),
                ha='center',
                va='bottom'
            )
        
        # Plot 2: Histogram of interarrival times
        ax2.hist(data['interarrival_times'], bins=20, 
                color='skyblue', edgecolor='black')
        ax2.set_title('Distribution of Interarrival Times')
        ax2.set_xlabel('Interarrival Time (minutes)')
        ax2.set_ylabel('Frequency')
        
        plt.tight_layout()
        return plt

# Example usage and simulation
def demonstrate_interarrivals():
    visualizer = InterarrivalVisualizer()
    
    # Simulate a coffee shop with average of 30 customers per hour
    data = visualizer.simulate_customer_arrivals(
        num_customers=50,
        avg_arrival_rate=30
    )
    
    # Calculate some statistics
    stats = {
        'mean_interarrival': np.mean(data['interarrival_times']),
        'std_interarrival': np.std(data['interarrival_times']),
        'min_interarrival': np.min(data['interarrival_times']),
        'max_interarrival': np.max(data['interarrival_times'])
    }
    
    # Create visualization
    visualizer.visualize_arrivals_and_interarrivals(data)
    
    print("\nInterarrival Time Statistics (in minutes):")
    print(f"Average time between customers: {stats['mean_interarrival']:.1f}")
    print(f"Standard deviation: {stats['std_interarrival']:.1f}")
    print(f"Minimum time between customers: {stats['min_interarrival']:.1f}")
    print(f"Maximum time between customers: {stats['max_interarrival']:.1f}")

if __name__ == "__main__":
    demonstrate_interarrivals()
```

## 1.2 Why Are Interarrival Times Important?

Interarrival times are crucial in Queueing Theory because they help us:

1. **Predict System Load**: 
   - Short interarrival times → high system load
   - Long interarrival times → low system load

2. **Plan Resource Allocation**:
   ```python
   def calculate_server_utilization(
       avg_interarrival_time: float,
       avg_service_time: float) -> float:
       """
       Calculate server utilization
       
       Parameters:
       avg_interarrival_time: Average time between arrivals (minutes)
       avg_service_time: Average time to serve each customer (minutes)
       
       Returns:
       Utilization rate (0 to 1)
       """
       return avg_service_time / avg_interarrival_time
   ```

3. **Identify Patterns**:
   - Rush hours (shorter interarrivals)
   - Quiet periods (longer interarrivals)

## 1.3 Properties of Interarrival Times

In many real-world scenarios, interarrival times follow an exponential distribution because:
1. Arrivals are independent
2. The probability of an arrival is constant over short intervals
3. Two arrivals cannot occur exactly simultaneously

Let's verify this with real data:

```python
class InterarrivalAnalyzer:
    def test_exponential_distribution(self, 
                                    interarrival_times: List[float]) -> bool:
        """
        Test if interarrival times follow exponential distribution
        using Kolmogorov-Smirnov test
        """
        from scipy import stats
        
        # Fit exponential distribution
        loc, scale = stats.expon.fit(interarrival_times)
        
        # Perform KS test
        ks_statistic, p_value = stats.kstest(
            interarrival_times,
            'expon',
            args=(loc, scale)
        )
        
        return {
            'follows_exponential': p_value > 0.05,
            'p_value': p_value,
            'ks_statistic': ks_statistic
        }

# Example usage
def analyze_distribution():
    # Generate sample data
    data = np.random.exponential(scale=2, size=1000)
    
    analyzer = InterarrivalAnalyzer()
    results = analyzer.test_exponential_distribution(data)
    
    print("\nDistribution Analysis:")
    print(f"Follows exponential distribution: {results['follows_exponential']}")
    print(f"P-value: {results['p_value']:.4f}")
```

## 1.4 Practical Applications

1. **Restaurant Management**:
   - Planning staff schedules based on arrival patterns
   - Optimizing seating arrangements

2. **Call Center Operations**:
   - Determining required number of operators
   - Predicting peak load times

3. **Emergency Services**:
   - Allocating emergency vehicles
   - Positioning resources based on call patterns

## 1.5 Key Takeaways

1. Interarrival time is simply the time between consecutive arrivals
2. In many cases, these times follow an exponential distribution
3. Understanding interarrival patterns helps in resource planning
4. Real-world systems often have varying arrival rates
