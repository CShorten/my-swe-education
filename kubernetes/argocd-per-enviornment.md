# ArgoCD App Per Environment with Kustomize Overlays

https://argo-cd.readthedocs.io/en/stable/

## Directory Structure
```
├── base
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
├── overlays
│   ├── development
│   │   ├── kustomization.yaml
│   │   └── patch.yaml
│   ├── staging
│   │   ├── kustomization.yaml
│   │   └── patch.yaml
│   └── production
│       ├── kustomization.yaml
│       └── patch.yaml
└── argocd
    ├── development.yaml
    ├── staging.yaml
    └── production.yaml
```

## Base Configuration

### base/deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: my-app
        image: my-app:1.0.0
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"
```

### base/kustomization.yaml
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
```

## Environment Overlays

### overlays/development/kustomization.yaml
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
bases:
  - ../../base
namePrefix: dev-
namespace: development
patchesStrategicMerge:
  - patch.yaml
```

### overlays/development/patch.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: my-app
        image: my-app:dev
        env:
        - name: ENVIRONMENT
          value: development
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
```

### overlays/production/kustomization.yaml
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
bases:
  - ../../base
namePrefix: prod-
namespace: production
patchesStrategicMerge:
  - patch.yaml
```

### overlays/production/patch.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: my-app
        image: my-app:prod
        env:
        - name: ENVIRONMENT
          value: production
        resources:
          requests:
            memory: "128Mi"
            cpu: "500m"
          limits:
            memory: "256Mi"
            cpu: "1000m"
```

## ArgoCD Applications

### argocd/development.yaml
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app-dev
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/my-org/my-app.git
    targetRevision: HEAD
    path: overlays/development
  destination:
    server: https://kubernetes.default.svc
    namespace: development
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### argocd/production.yaml
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/my-org/my-app.git
    targetRevision: HEAD
    path: overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: false  # Require manual approval for production
    syncOptions:
    - CreateNamespace=true
```

## Key Concepts

1. **Base Configuration**: 
   - Contains the common configuration shared across all environments
   - Defines the core Kubernetes resources (deployments, services, etc.)

2. **Overlays**:
   - Environment-specific modifications using Kustomize
   - Can override or add to the base configuration
   - Common customizations include:
     - Resource limits
     - Replica counts
     - Environment variables
     - Image tags
     - Namespace settings

3. **ArgoCD Applications**:
   - One Application per environment
   - Points to the specific overlay directory
   - Can have different sync policies per environment
   - Allows for independent deployment and rollback

4. **Benefits**:
   - Clear separation of environments
   - Environment-specific configurations
   - Independent deployment cycles
   - Different policies per environment
   - Easy rollback per environment
   - Configuration reuse through base/overlay pattern

5. **Best Practices**:
   - Keep base configurations minimal
   - Use patches for environment-specific changes
   - Implement stricter sync policies for production
   - Use separate namespaces per environment
   - Version control all configurations
   - Document environment differences
   - Use consistent naming conventions
