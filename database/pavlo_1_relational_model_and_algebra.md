# 01 - Relational Model & Algebra

[Link](https://www.youtube.com/watch?v=APqWIjtzNGE)

### What is a DBMS trying to do for you?

### Example -- Digital Music

```python
class Aritst(BaseModel):
  name: str
  year: int
  country: enum
```

### Read files

Ah! This is so slow!!

```python
for line in file.readlines():
  record = parse(line)
  if record[0] == "GZA":
    print(int(record[1]))
```


