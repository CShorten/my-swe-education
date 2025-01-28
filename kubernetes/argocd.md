# ArgoCD Setup Guide

This guide walks through the process of setting up ArgoCD, a declarative continuous delivery tool for Kubernetes.

## Prerequisites

- Kubernetes cluster (version 1.16+)
- kubectl configured with cluster access
- helm (optional, for helm chart installation)

## 1. Installation

### Using kubectl

```bash
# Create a new namespace for ArgoCD
kubectl create namespace argocd

# Apply the installation manifest
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

### Using Helm (Alternative)

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
helm install argocd argo/argo-cd -n argocd --create-namespace
```

## 2. Access the ArgoCD UI

### Port Forwarding
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

The UI will be available at: https://localhost:8080

### Getting Initial Admin Credentials
```bash
# Retrieve the auto-generated admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

## 3. CLI Installation

### MacOS
```bash
brew install argocd
```

### Linux
```bash
curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo install -m 555 argocd /usr/local/bin/argocd
```

### Windows
```bash
# Download the latest version from:
# https://github.com/argoproj/argo-cd/releases/latest
# Extract and add to PATH
```

## 4. CLI Login

```bash
# Login using the CLI
argocd login localhost:8080

# Change the admin password
argocd account update-password
```

## 5. Creating Your First Application

### Using CLI
```bash
argocd app create my-app \
  --repo https://github.com/your-org/your-repo.git \
  --path path/to/your/manifests \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace default
```

### Using YAML
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
  namespace: argocd
spec:
  destination:
    namespace: default
    server: https://kubernetes.default.svc
  project: default
  source:
    path: path/to/your/manifests
    repoURL: https://github.com/your-org/your-repo.git
    targetRevision: HEAD
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

Save this as `application.yaml` and apply:
```bash
kubectl apply -f application.yaml
```

## 6. Advanced Configuration

### SSL/TLS Configuration
```bash
# Generate TLS certificates
kubectl -n argocd create secret tls argocd-server-tls \
  --cert=/path/to/cert.pem \
  --key=/path/to/key.pem
```

### SSO Configuration
Add to the argocd-cm ConfigMap:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cm
  namespace: argocd
data:
  url: https://argocd.example.com
  dex.config: |
    connectors:
      - type: github
        id: github
        name: GitHub
        config:
          clientID: your-client-id
          clientSecret: your-client-secret
          orgs:
          - name: your-github-org
```

### RBAC Configuration
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
data:
  policy.csv: |
    p, role:org-admin, applications, *, */*, allow
    p, role:org-admin, clusters, get, *, allow
    p, role:org-admin, projects, *, *, allow
    g, your-github-org:team-name, role:org-admin
```

## 7. Health Checks and Monitoring

### Prometheus Metrics
ArgoCD exposes Prometheus metrics at:
```
https://argocd-server-metrics:8082/metrics
```

### Adding Custom Health Checks
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cm
  namespace: argocd
data:
  resource.customizations: |
    argoproj.io/Application:
      health.lua: |
        hs = {}
        hs.status = "Progressing"
        hs.message = ""
        if obj.status ~= nil then
          if obj.status.health ~= nil then
            hs.status = obj.status.health.status
            hs.message = obj.status.health.message
          end
        end
        return hs
```

## Troubleshooting

### Common Issues and Solutions

1. **UI Not Accessible**
```bash
# Check if pods are running
kubectl get pods -n argocd

# Check server logs
kubectl logs -n argocd deploy/argocd-server
```

2. **Sync Issues**
```bash
# Check application status
argocd app get my-app

# Force sync
argocd app sync my-app --force
```

3. **Authentication Issues**
```bash
# Reset admin password
kubectl -n argocd patch secret argocd-secret \
  -p '{"stringData": {
    "admin.password": "$2a$10$new-password-hash",
    "admin.passwordMtime": "'$(date +%FT%T%Z)'"
  }}'
```

## Best Practices

1. Always use declarative application definitions
2. Implement automated sync policies carefully
3. Use projects to organize applications and implement security boundaries
4. Regularly backup ArgoCD configurations
5. Monitor sync status and implement alerts
6. Use helm hooks or wave annotations for controlling sync order
7. Implement proper RBAC from the start

## Security Considerations

1. Change the default admin password immediately
2. Configure TLS for the ArgoCD server
3. Implement SSO when possible
4. Use RBAC to limit access
5. Regularly update ArgoCD to the latest version
6. Limit access to the argocd namespace
7. Use network policies to restrict pod communication
