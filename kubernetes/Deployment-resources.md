The `resources` section specifies the computational resources that each Pod in this Deployment can use:

```yaml
resources:
  requests:
    cpu: 250m
    memory: 1.5Gi
  limits:
    cpu: 400m
    memory: 4Gi
```

1. `requests` - These are guaranteed resources that K8s will reserve for your Pod

- `250m` CPU means 0.25 of a CPU core (m stands for "millicore", where 1000m = 1 core)
- `1.5Gi` memory is what the Pod expects to need for normal operation.

2. `limits` - These are the maximum resources your Pod can burst to

- `4000m` CPU means 4 full CPU cores
- `4Gi` memory is the hard limit
