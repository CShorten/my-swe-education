# `.extend()`

The .extend() method lets you add multiple items from an iterable (like a list, tuple, or set) to the end of an existing list. Here's how to use it:

Basic Usage:

```python
pythonCopyfruits = ['apple', 'banana']
more_fruits = ['orange', 'grape']
fruits.extend(more_fruits)
print(fruits)  # ['apple', 'banana', 'orange', 'grape']
```

Key Differences from .append():

```python
# Using append() adds the entire list as a single element
list1 = [1, 2]
list1.append([3, 4])
print(list1)  # [1, 2, [3, 4]]

# Using extend() adds each element individually
list2 = [1, 2]
list2.extend([3, 4])
print(list2)  # [1, 2, 3, 4]
```
Important things to remember:

.extend() modifies the original list in-place
It only works with iterables
The order of elements is preserved
It's more efficient than using + or += for multiple additions
