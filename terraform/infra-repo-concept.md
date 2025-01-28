# Infrastructure Repository Guide

## Typical Structure
```
infrastructure-repo/
├── README.md
├── clusters/
│   ├── development/
│   │   ├── argocd/
│   │   │   ├── applications/
│   │   │   └── projects/
│   │   ├── cert-manager/
│   │   │   ├── cluster-issuers.yaml
│   │   │   └── values.yaml
│   │   ├── external-dns/
│   │   │   └── values.yaml
│   │   ├── ingress-nginx/
│   │   │   └── values.yaml
│   │   ├── monitoring/
│   │   │   ├── grafana-values.yaml
│   │   │   └── prometheus-values.yaml
│   │   └── sealed-secrets/
│   │       └── controller.yaml
│   └── production/
│       └── [similar structure to development]
├── platform/
│   ├── cert-manager/
│   │   ├── base/
│   │   └── overlays/
│   ├── external-dns/
│   │   ├── base/
│   │   └── overlays/
│   └── monitoring/
│       ├── base/
│       └── overlays/
└── scripts/
    └── bootstrap/
        └── install.sh

```

## Key Components

### 1. Cluster-Level Configurations (clusters/)
```yaml
# clusters/development/argocd/applications/cert-manager.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: cert-manager
  namespace: argocd
spec:
  project: platform-services
  source:
    repoURL: https://github.com/company/infrastructure-repo.git
    path: platform/cert-manager/overlays/development
    targetRevision: HEAD
  destination:
    server: https://kubernetes.default.svc
    namespace: cert-manager
```

### 2. Platform Services (platform/)
```yaml
# platform/monitoring/base/prometheus.yaml
apiVersion: monitoring.coreos.com/v1
kind: Prometheus
metadata:
  name: prometheus
spec:
  replicas: 2
  storage:
    volumeClaimTemplate:
      spec:
        resources:
          requests:
            storage: 100Gi
```

### 3. Environment-Specific Values
```yaml
# clusters/development/monitoring/prometheus-values.yaml
prometheus:
  resources:
    requests:
      cpu: 1
      memory: 2Gi
    limits:
      cpu: 2
      memory: 4Gi
  retention: 15d
```

## Common Use Cases

### 1. Platform Service Management
```yaml
# Platform service ArgoCD application
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: platform-services
  namespace: argocd
spec:
  project: platform
  source:
    repoURL: https://github.com/company/infrastructure-repo.git
    path: clusters/development/platform-services
  destination:
    server: https://kubernetes.default.svc
```

### 2. Application Deployment Definitions
```yaml
# Application deployment configuration
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: team-a-apps
  namespace: argocd
spec:
  project: team-a
  source:
    repoURL: https://github.com/company/team-a-apps.git
    path: apps/overlays/development
  destination:
    server: https://kubernetes.default.svc
    namespace: team-a
```

### 3. Shared Resources
```yaml
# Network policies, resource quotas, etc.
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-quota
spec:
  hard:
    cpu: "20"
    memory: 40Gi
    pods: "50"
```

## Key Benefits

1. **Centralized Infrastructure Management**
   - Single source of truth for infrastructure
   - Version controlled configuration
   - Clear audit trail of changes

2. **Environment Parity**
   - Consistent configuration across environments
   - Easy to replicate environments
   - Clear visibility of environment differences

3. **Security and Compliance**
   - RBAC configurations in version control
   - Security policies as code
   - Compliance requirements documented

4. **Disaster Recovery**
   - Complete cluster configuration backed up
   - Easy to rebuild environments
   - Dependencies documented

## Best Practices

1. **Repository Organization**
   - Clear separation of cluster vs platform configs
   - Environment-specific configurations isolated
   - Shared configurations in base directories

2. **Change Management**
   - Use pull requests for changes
   - Implement review requirements
   - Automated validation in CI/CD

3. **Documentation**
   - README files in each directory
   - Architecture diagrams
   - Dependency documentation

4. **Security**
   - Sensitive data in sealed secrets
   - RBAC policies version controlled
   - Regular security audits

## Common Patterns

1. **Multi-Cluster Management**
   - Separate directories per cluster
   - Shared platform configurations
   - Cluster-specific overrides

2. **Platform Services**
   - Base configurations in platform/
   - Environment overlays in clusters/
   - Helm values per environment

3. **Application Definitions**
   - ArgoCD applications in clusters/*/argocd/applications/
   - Team projects in clusters/*/argocd/projects/
   - Shared resources in clusters/*/shared/
