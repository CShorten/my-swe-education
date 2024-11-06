# GPU Memory Optimization in Python using Numba CUDA

## Introduction
While traditional CUDA requires C/C++, Python developers can leverage GPU acceleration using Numba's CUDA capabilities. This report explores memory coalescing and optimization techniques using Python-friendly tools.

## Numba CUDA Basics
Numba allows you to write GPU code in Python by adding decorators to your functions. Here's a simple example:

```python
from numba import cuda
import numpy as np

@cuda.jit
def basic_kernel(input_arr, output_arr):
    idx = cuda.grid(1)  # Get the 1D grid index
    if idx < input_arr.shape[0]:
        output_arr[idx] = input_arr[idx] * 2.0
```

## Memory Access Patterns

### Coalesced Access Pattern
```python
@cuda.jit
def coalesced_access(input_arr, output_arr):
    idx = cuda.grid(1)
    if idx < input_arr.shape[0]:
        # Threads access consecutive memory locations
        output_arr[idx] = input_arr[idx] * 2.0
```

### Non-Coalesced Access Pattern
```python
@cuda.jit
def non_coalesced_access(input_arr, output_arr):
    idx = cuda.grid(1)
    if idx < input_arr.shape[0]:
        # Threads access memory with stride, reducing performance
        stride = 32
        if idx * stride < input_arr.shape[0]:
            output_arr[idx] = input_arr[idx * stride] * 2.0
```

## Using Shared Memory in Python
Shared memory is a key optimization technique in GPU programming:

```python
@cuda.jit
def shared_memory_example(input_arr, output_arr):
    # Declare shared memory
    shared_arr = cuda.shared.array(shape=(256,), dtype=float32)
    
    tx = cuda.threadIdx.x
    bx = cuda.blockIdx.x
    block_size = cuda.blockDim.x
    
    # Global index
    idx = bx * block_size + tx
    
    if idx < input_arr.shape[0]:
        # Load data into shared memory
        shared_arr[tx] = input_arr[idx]
        
        # Ensure all threads have loaded their data
        cuda.syncthreads()
        
        # Process data in shared memory
        shared_arr[tx] *= 2.0
        
        # Write back to global memory
        output_arr[idx] = shared_arr[tx]
```

## Matrix Operations Example
Here's a practical example of matrix transpose optimization:

```python
@cuda.jit
def matrix_transpose(input_matrix, output_matrix):
    # Get 2D thread and block indices
    tx = cuda.threadIdx.x
    ty = cuda.threadIdx.y
    bx = cuda.blockIdx.x
    by = cuda.blockIdx.y
    
    # Declare shared memory with padding to avoid bank conflicts
    TILE_DIM = 32
    shared = cuda.shared.array(shape=(TILE_DIM, TILE_DIM+1), dtype=float32)
    
    # Calculate global indices
    x = bx * TILE_DIM + tx
    y = by * TILE_DIM + ty
    
    # Load data into shared memory
    if x < input_matrix.shape[1] and y < input_matrix.shape[0]:
        shared[ty, tx] = input_matrix[y, x]
    
    cuda.syncthreads()
    
    # Calculate transposed indices
    x = by * TILE_DIM + tx
    y = bx * TILE_DIM + ty
    
    # Write transposed data
    if x < input_matrix.shape[0] and y < input_matrix.shape[1]:
        output_matrix[y, x] = shared[tx, ty]
```

## Performance Measurement
Here's how to benchmark your GPU kernels:

```python
import numpy as np
from numba import cuda
import time

def benchmark_kernel(kernel_func, input_size):
    # Prepare data
    input_data = np.random.random(input_size).astype(np.float32)
    output_data = np.zeros_like(input_data)
    
    # Copy to GPU
    d_input = cuda.to_device(input_data)
    d_output = cuda.to_device(output_data)
    
    # Set up grid and block dimensions
    threads_per_block = 256
    blocks_per_grid = (input_size + threads_per_block - 1) // threads_per_block
    
    # Warm-up run
    kernel_func[blocks_per_grid, threads_per_block](d_input, d_output)
    
    # Timing
    start = time.perf_counter()
    for _ in range(100):
        kernel_func[blocks_per_grid, threads_per_block](d_input, d_output)
    cuda.synchronize()
    end = time.perf_counter()
    
    return (end - start) / 100  # Average time per run
```

## Best Practices for Python GPU Programming

1. **Data Transfer Optimization**
```python
# Bad: Frequent small transfers
for i in range(1000):
    d_array = cuda.to_device(host_array[i])
    kernel[block_dim, grid_dim](d_array)
    
# Good: Single large transfer
d_array = cuda.to_device(host_array)
kernel[block_dim, grid_dim](d_array)
```

2. **Memory Layout**
```python
# Bad: Array of structures
class Particle:
    def __init__(self, x, y, z, velocity):
        self.x = x
        self.y = y
        self.z = z
        self.velocity = velocity

# Good: Structure of arrays
x = np.array([...])
y = np.array([...])
z = np.array([...])
velocity = np.array([...])
```

3. **Grid and Block Size Selection**
```python
def calculate_grid_dim(size):
    threads_per_block = 256  # Multiple of 32 (warp size)
    blocks = (size + threads_per_block - 1) // threads_per_block
    return blocks, threads_per_block
```

## Common Pitfalls to Avoid

1. **Global Memory Access Patterns**
   - Ensure aligned memory access
   - Use contiguous arrays when possible
   - Avoid strided access patterns

2. **Synchronization**
   - Only use `cuda.syncthreads()` when necessary
   - Ensure all threads in a block reach synchronization points

3. **Data Types**
   - Use appropriate data types (float32 vs float64)
   - Be aware of type conversion overhead

## Conclusion
While Python with Numba may not offer the same low-level control as C++ CUDA, it provides a more accessible way to leverage GPU acceleration while maintaining good performance through proper memory access patterns and optimization techniques.

## References
1. Numba Documentation
2. "Python High Performance" by Gabriele Lanaro
3. NVIDIA CUDA Python Documentation
4. Numba CUDA User Guide
