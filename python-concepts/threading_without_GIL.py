'''
The Experimental Free-threaded Mode in Python 3.13 represents a major step toward improving 
multi-threaded performance by removing the Global Interpreter Lock (GIL). 
Traditionally, the GIL has been a limiting factor in Python’s threading model, 
as it allows only one thread to execute Python bytecode at a time, even on multi-core systems. 
This new mode, when enabled, allows multiple threads to execute concurrently without the GIL, 
offering the potential for much better CPU-bound performance in multi-threaded applications.

Though still experimental and available only in select builds (Windows and macOS), 
this feature lays the groundwork for making Python more suitable for multi-core processors. 
It is particularly beneficial in scenarios like I/O-bound operations and parallel computations, 
where more concurrent execution can significantly improve overall performance.

This development is part of Python's long-term effort to enhance threading and concurrency
'''

import threading

def print_numbers():
    for i in range(10):
        print(i)

def print_letters():
    for letter in 'abcdefghij':
        print(letter)

# Create threads
thread1 = threading.Thread(target=print_numbers)
thread2 = threading.Thread(target=print_letters)

# Start threads
thread1.start()
thread2.start()

# Join threads
thread1.join()
thread2.join()
