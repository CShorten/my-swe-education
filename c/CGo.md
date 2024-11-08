# Integrating C++ with Go Using CGo: A Comprehensive Guide

## Introduction
CGo allows Go programs to call C code, but integrating C++ requires additional considerations due to name mangling and object-oriented features. This guide demonstrates how to successfully integrate C++ code into Go applications.

## Basic CGo Setup

### Directory Structure
```
project/
├── cpp/
│   ├── calculator.hpp
│   ├── calculator.cpp
│   └── wrapper.cpp
├── main.go
└── calculator.go
```

### Example 1: Simple C++ Class Integration

First, let's create a simple C++ class (`calculator.hpp`):

```cpp
// calculator.hpp
#ifndef CALCULATOR_HPP
#define CALCULATOR_HPP

class Calculator {
public:
    Calculator();
    double add(double a, double b);
    double subtract(double a, double b);
private:
    int precision;
};

#endif
```

Implementation (`calculator.cpp`):

```cpp
// calculator.cpp
#include "calculator.hpp"

Calculator::Calculator() : precision(2) {}

double Calculator::add(double a, double b) {
    return a + b;
}

double Calculator::subtract(double a, double b) {
    return a - b;
}
```

### C Wrapper

To bridge C++ and Go, we need a C wrapper (`wrapper.cpp`):

```cpp
// wrapper.cpp
#include "calculator.hpp"
#include <cstdlib>

extern "C" {
    typedef void* calculator_t;
    
    calculator_t calculator_new() {
        return new Calculator();
    }
    
    double calculator_add(calculator_t calc, double a, double b) {
        return static_cast<Calculator*>(calc)->add(a, b);
    }
    
    double calculator_subtract(calculator_t calc, double a, double b) {
        return static_cast<Calculator*>(calc)->subtract(a, b);
    }
    
    void calculator_free(calculator_t calc) {
        delete static_cast<Calculator*>(calc);
    }
}
```

### Go Integration

Create the Go wrapper (`calculator.go`):

```go
package main

// #cgo CXXFLAGS: -std=c++11
// #cgo LDFLAGS: -lstdc++
// #include <stdlib.h>
// typedef void* calculator_t;
// calculator_t calculator_new();
// double calculator_add(calculator_t calc, double a, double b);
// double calculator_subtract(calculator_t calc, double a, double b);
// void calculator_free(calculator_t calc);
import "C"
import "runtime"

type Calculator struct {
    handle C.calculator_t
}

func NewCalculator() *Calculator {
    calc := &Calculator{handle: C.calculator_new()}
    runtime.SetFinalizer(calc, (*Calculator).Free)
    return calc
}

func (c *Calculator) Add(a, b float64) float64 {
    return float64(C.calculator_add(c.handle, C.double(a), C.double(b)))
}

func (c *Calculator) Subtract(a, b float64) float64 {
    return float64(C.calculator_subtract(c.handle, C.double(a), C.double(b)))
}

func (c *Calculator) Free() {
    if c.handle != nil {
        C.calculator_free(c.handle)
        c.handle = nil
    }
}
```

### Usage Example (`main.go`):

```go
package main

import "fmt"

func main() {
    calc := NewCalculator()
    
    result1 := calc.Add(10.5, 5.2)
    result2 := calc.Subtract(15.7, 3.2)
    
    fmt.Printf("Addition: %.2f\n", result1)
    fmt.Printf("Subtraction: %.2f\n", result2)
}
```

## Advanced Example: Template and STL Integration

Here's a more complex example using C++ templates and STL:

```cpp
// vector_ops.hpp
#ifndef VECTOR_OPS_HPP
#define VECTOR_OPS_HPP

#include <vector>
#include <string>

template <typename T>
class VectorOps {
public:
    std::vector<T> data;
    void push(T value);
    T sum();
    size_t size();
};

#endif
```

Implementation:

```cpp
// vector_ops.cpp
#include "vector_ops.hpp"

template <typename T>
void VectorOps<T>::push(T value) {
    data.push_back(value);
}

template <typename T>
T VectorOps<T>::sum() {
    T result = T();
    for (const T& val : data) {
        result += val;
    }
    return result;
}

template <typename T>
size_t VectorOps<T>::size() {
    return data.size();
}

// Explicit template instantiation
template class VectorOps<int>;
template class VectorOps<double>;
```

C Wrapper for the template class:

```cpp
// vector_wrapper.cpp
#include "vector_ops.hpp"

extern "C" {
    typedef void* vector_ops_int_t;
    typedef void* vector_ops_double_t;
    
    vector_ops_int_t vector_ops_int_new() {
        return new VectorOps<int>();
    }
    
    vector_ops_double_t vector_ops_double_new() {
        return new VectorOps<double>();
    }
    
    void vector_ops_int_push(vector_ops_int_t v, int value) {
        static_cast<VectorOps<int>*>(v)->push(value);
    }
    
    void vector_ops_double_push(vector_ops_double_t v, double value) {
        static_cast<VectorOps<double>*>(v)->push(value);
    }
    
    int vector_ops_int_sum(vector_ops_int_t v) {
        return static_cast<VectorOps<int>*>(v)->sum();
    }
    
    double vector_ops_double_sum(vector_ops_double_t v) {
        return static_cast<VectorOps<double>*>(v)->sum();
    }
    
    void vector_ops_int_free(vector_ops_int_t v) {
        delete static_cast<VectorOps<int>*>(v);
    }
    
    void vector_ops_double_free(vector_ops_double_t v) {
        delete static_cast<VectorOps<double>*>(v);
    }
}
```

## Building and Compilation

To build the project, you'll need to compile the C++ code into a shared library first:

```bash
# Compile C++ files
g++ -c -fPIC calculator.cpp wrapper.cpp vector_ops.cpp vector_wrapper.cpp
g++ -shared -o libcalculator.so calculator.o wrapper.o vector_ops.o vector_wrapper.o

# Build Go program
go build -o myprogram main.go calculator.go
```

## Best Practices and Considerations

1. **Memory Management**
   - Always free C++ objects when they're no longer needed
   - Use runtime.SetFinalizer in Go to ensure cleanup
   - Be careful with sharing pointers between Go and C++

2. **Error Handling**
   - C++ exceptions don't cross the C boundary well
   - Implement error codes or status returns in the C wrapper
   - Check for null pointers and invalid states

3. **Performance**
   - Minimize crossings between Go and C++
   - Batch operations when possible
   - Consider using arrays instead of individual values for bulk operations

4. **Thread Safety**
   - Ensure C++ code is thread-safe if called from multiple goroutines
   - Consider using mutex locks in the wrapper layer
   - Be aware of Go's runtime scheduler interaction with C calls

## Common Pitfalls

1. **Name Mangling**
   - Always use extern "C" for wrapper functions
   - Keep C++ class definitions in header files
   - Use proper linkage specifications

2. **Build Issues**
   - Include all necessary C++ runtime libraries
   - Set correct compiler and linker flags
   - Maintain consistent ABI across builds

3. **Memory Leaks**
   - Track object creation and destruction
   - Use smart pointers in C++ code
   - Implement proper cleanup in Go code

## Conclusion

CGo provides a powerful way to integrate C++ code into Go applications, but it requires careful attention to memory management, build configuration, and performance considerations. By following these patterns and best practices, you can successfully bridge the gap between Go and C++ while maintaining safety and efficiency.
