### file structure overview

```
temporal-k8s/
├── src/
│   ├── activities.py
│   ├── workflows.py
│   ├── worker.py
│   ├── starter.py
│   └── utils/
│       ├── monitoring.py
│       └── temporal_client.py
├── docker/
│   ├── worker.Dockerfile
│   └── orchestrator.Dockerfile
├── k8s/
│   ├── worker/
│   │   ├── deployment.yaml
│   │   ├── configmap.yaml
│   │   ├── secret.yaml
│   │   └── hpa.yaml
│   └── orchestrator/
│       ├── deployment.yaml
│       ├── configmap.yaml
│       └── secret.yaml
├── requirements.txt
└── README.md
```

### 20 Quick Concepts to get up to speed with this:
1. Worker-Orchestrator Separation: The worker and orchestrator deployments should run in separate pods, as they serve different purposes. Workers execute activities, while orchestrators start workflows.
2. Certificate Management: Temporal Cloud certificates should be stored as Kubernetes secrets and mounted into both worker and orchestrator pods. Never bake certificates into container images.
3. Deployment Scaling: Workers can be horizontally scaled with multiple replicas, but orchestrators typically need fewer replicas as they only initiate workflows.
4. Resource Allocation: Workers need more resources as they perform actual work, while orchestrators are typically lighter as they only coordinate.
5. Health Monitoring: Both workers and orchestrators should implement health checks (liveness and readiness probes) to help Kubernetes manage them effectively.
6. Metrics Collection: Use Prometheus metrics to track workflow starts, completions, and failures. These metrics can inform scaling decisions.
7. High Availability: Run workers across multiple availability zones using pod anti-affinity rules to ensure resilience.
8. Network Policy: Implement Kubernetes network policies to control which pods can communicate with Temporal and each other.
9. Autoscaling Configuration: The HorizontalPodAutoscaler should be applied to the worker deployment, not the orchestrator, as workers need to scale with load.
10. Pod Disruption Budgets: Use PodDisruptionBudgets to ensure a minimum number of workers are always available during cluster maintenance.
11. ConfigMap Usage: Store Temporal configuration (namespace, task queue, etc.) in ConfigMaps, making it easy to modify without rebuilding containers.
12. Resource Limits: Always set both resource requests and limits to prevent pods from consuming too many cluster resources.
13. Logging Configuration: Configure worker and orchestrator pods to use the cluster's logging infrastructure (like EFK stack or CloudWatch).
14. Init Containers: Use init containers if you need to perform setup tasks before workers or orchestrators start (like checking dependencies).
15. Readiness Gates: Implement custom readiness gates if you need complex logic to determine when pods are ready to accept work.
16. Graceful Shutdown: Handle SIGTERM signals properly to ensure workflows and activities can complete or checkpoint their state before pod termination.
17. Service Accounts: Create specific Kubernetes service accounts for workers and orchestrators with appropriate RBAC permissions.
18. Liveness Probe Design: Make liveness probes lightweight to avoid false positives that could cause unnecessary pod restarts.
19. Readiness Probe Implementation: Include Temporal connectivity checks in readiness probes to ensure pods don't receive work until fully ready.
20. Deployment Strategy: Use rolling updates with appropriate maxSurge and maxUnavailable settings to ensure smooth deployments without workflow interruption.
