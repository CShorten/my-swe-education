# Python Decorators

### Introduction
Python decorators are a powerful feature that allows you to modify the behavior of functions or classes without changing their actual code. They provide a flexible way to extend functionality, making your code more modular and easier to maintain. This report explains how Python decorators work, provides examples, and demonstrates how to create custom decorators, including scenarios where they are particularly useful.

### What Are Decorators?
In Python, a decorator is a function that takes another function as an argument, adds some kind of functionality, and returns another function. All of this happens without altering the source code of the original function you passed in.

Decorators allow you to wrap another function in order to extend the behavior of the wrapped function, without permanently modifying it.

# Key Concepts
### First-Class Functions: Functions in Python are treated as first-class citizens. This means they can be passed around and used as arguments, just like any other object (strings, integers, etc.).

### Higher-Order Functions: A function that takes another function as an argument or returns one as a result.

## How Do Decorators Work?
A decorator is implemented as a callable (function, method, or class) that takes a callable object as an input and returns another callable object.

Basic Structure of a Decorator

```python
def my_decorator(func):
    def wrapper(*args, **kwargs):
        # Code to execute before calling the original function
        result = func(*args, **kwargs)
        # Code to execute after calling the original function
        return result
    return wrapper
```

func: The original function that you are decorating.
wrapper: The new function that adds some functionality before and/or after calling func.

## Applying a Decorator
You can apply a decorator to a function in two ways:

Manual Decoration:

```python
def greet():
    print("Hello!")
```

greet = my_decorator(greet)

## Using the @ Syntax:

```python
@my_decorator
def greet():
    print("Hello!")
```


The @ syntax is syntactic sugar for the manual decoration and is the preferred way to apply decorators.

Syntactic sugar is a term used in programming to describe syntax that makes code easier to read and write but doesn't add new functionality to the language. It allows developers to express operations in a more concise and human-readable way without changing how the code executes under the hood.

In the context of Python decorators, the @ symbol is considered syntactic sugar because it provides a more convenient and cleaner way to apply a decorator to a function or method. It simplifies the process by eliminating the need to manually wrap the original function with the decorator.
  
Examples of Built-in Decorators
Python provides several built-in decorators that you might already be familiar with.

@staticmethod and @classmethod
Used in classes to define methods that are not connected to a class instance.

```python
class MyClass:
    @staticmethod
    def static_method():
        print("This is a static method.")

    @classmethod
    def class_method(cls):
        print(f"This is a class method of {cls}.")
```

@property
Allows you to define methods in a class that can be accessed like attributes.

```python
class Circle:
    def __init__(self, radius):
        self._radius = radius

    @property
    def area(self):
        return 3.1416 * (self._radius ** 2)
```

Creating a Custom Decorator
Creating custom decorators allows you to add specific functionality that is tailored to your needs.

# Example: Logging Decorator
Let's create a decorator that logs the execution of a function.

```python
def logger(func):
    def wrapper(*args, **kwargs):
        print(f"Function '{func.__name__}' started with args: {args} and kwargs: {kwargs}")
        result = func(*args, **kwargs)
        print(f"Function '{func.__name__}' ended with result: {result}")
        return result
    return wrapper
```

## Applying the logger Decorator

```python
@logger
def add(a, b):
    return a + b

add(5, 3)
```

Function 'add' started with args: (5, 3) and kwargs: {}
Function 'add' ended with result: 8

## Explanation

logger: The decorator function that takes the original function func as an argument.
wrapper: A nested function that logs information before and after calling func.
*args, **kwargs: Allows the wrapper to accept any number of positional and keyword arguments.
When to Use Custom Decorators
Custom decorators are useful when you need to apply the same code pattern to multiple functions or methods. They help keep your code DRY (Don't Repeat Yourself) and improve readability.

## Common Use Cases
Logging and Debugging: Automatically log entry, exit, and errors in functions.

Authentication and Authorization: Check user permissions before executing a function.

Timing Functions: Measure the execution time of functions for performance analysis.

Caching: Store results of expensive function calls and return the cached result when the same inputs occur again.

# Advanced Example: Authentication Decorator
Imagine you are building a web application, and you want to restrict access to certain functions based on user roles.

```python
def requires_role(role):
    def decorator(func):
        def wrapper(user, *args, **kwargs):
            if user.role != role:
                raise PermissionError(f"User does not have the required role: {role}")
            return func(user, *args, **kwargs)
        return wrapper
    return decorator
```

## Applying the Decorator

```python
@requires_role('admin')
def delete_user(user, user_id):
    print(f"User {user_id} has been deleted by {user.username}")
```

```python
class User:
    def __init__(self, username, role):
        self.username = username
        self.role = role

admin_user = User('admin_user', 'admin')
regular_user = User('regular_user', 'user')

# This will work
delete_user(admin_user, 123)

# This will raise PermissionError
delete_user(regular_user, 123)
```

## Explanation
requires_role: A decorator factory that accepts a role parameter.
decorator: The actual decorator that will be applied to the function.
wrapper: Checks if the user has the required role before executing the function.
Why Use This Decorator?
This approach centralizes the authentication logic, making it easy to apply the same security checks across multiple functions without code duplication.

Understanding Decorator Internals
Decorators can sometimes be confusing, especially when dealing with function metadata like __name__ and __doc__.

Preserving Metadata with functools.wraps
When you decorate a function, the original function's metadata is lost because the wrapper function replaces it.

# Key Takeaways:

Decorators wrap a function to modify or extend its behavior.
They promote code reuse and adhere to the DRY principle.
Custom decorators can be tailored to fit specific needs in your application.
