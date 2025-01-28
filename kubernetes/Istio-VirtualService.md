VirtualService offers more sophisticated traffic management features than what Kubernetes offers out of the box with basic HTTP routing.

You have this kind of:

```
spec:
  http:
  - route:
    - desitnation:
      host: `Kubernetes Service name`
      subset: `model1`
    weight: 90
    - destination:
      ...
```
