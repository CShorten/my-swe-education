# Deploying a Python Application with Kubernetes: A Step-by-Step Guide

## 1. Sample Python Application
First, let's create a simple Flask application to deploy.

**`app.py`**
```python
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello from Kubernetes!'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
```

**`requirements.txt`**
```
flask==2.0.1
gunicorn==20.1.0
```

## 2. Dockerfile
Create a Dockerfile to containerize the application.

**`Dockerfile`**
```dockerfile
# Use official Python runtime as base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Set environment variables
ENV PORT=5000

# Expose port
EXPOSE 5000

# Run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

## 3. Build and Push Docker Image
```bash
# Build the Docker image
docker build -t your-registry/python-k8s-app:v1 .

# Push to your container registry
docker push your-registry/python-k8s-app:v1
```

## 4. Kubernetes Manifests

### Pod Definition
**`pod.yaml`**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: python-app-pod
  labels:
    app: python-app
spec:
  containers:
  - name: python-app
    image: your-registry/python-k8s-app:v1
    ports:
    - containerPort: 5000
    resources:
      requests:
        memory: "64Mi"
        cpu: "250m"
      limits:
        memory: "128Mi"
        cpu: "500m"
```

### Deployment Manifest
**`deployment.yaml`**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-app-deployment
  labels:
    app: python-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: python-app
  template:
    metadata:
      labels:
        app: python-app
    spec:
      containers:
      - name: python-app
        image: your-registry/python-k8s-app:v1
        ports:
        - containerPort: 5000
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 10
```

### Service Manifest
**`service.yaml`**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: python-app-service
spec:
  selector:
    app: python-app
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5000
  type: LoadBalancer
```

## 5. Deployment Commands
Here are the commands to deploy your application to Kubernetes:

```bash
# Create namespace (optional)
kubectl create namespace python-app

# Apply the namespace to current context (if created)
kubectl config set-context --current --namespace=python-app

# Deploy the application
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# Verify deployment
kubectl get deployments
kubectl get pods
kubectl get services

# Check pod logs
kubectl logs -l app=python-app

# Scale deployment (optional)
kubectl scale deployment python-app-deployment --replicas=5

# Check deployment status
kubectl rollout status deployment/python-app-deployment
```

## 6. Common Operations and Troubleshooting

### Check Pod Status
```bash
# Get detailed pod information
kubectl describe pod <pod-name>

# Get pod logs
kubectl logs <pod-name>

# Execute commands in pod
kubectl exec -it <pod-name> -- /bin/bash
```

### Monitor Resources
```bash
# Get resource usage
kubectl top pods
kubectl top nodes

# Watch pod status
kubectl get pods -w
```

### Rolling Updates
```bash
# Update image
kubectl set image deployment/python-app-deployment python-app=your-registry/python-k8s-app:v2

# Rollback if needed
kubectl rollout undo deployment/python-app-deployment
```

## 7. Best Practices

1. **Resource Management**
   - Always specify resource requests and limits
   - Monitor resource usage regularly
   - Use horizontal pod autoscaling for scalability

2. **Health Checks**
   - Implement both liveness and readiness probes
   - Set appropriate timing for probes
   - Include meaningful health check endpoints

3. **Security**
   - Use private container registries
   - Implement RBAC (Role-Based Access Control)
   - Keep container images up to date

4. **Logging and Monitoring**
   - Implement structured logging
   - Use Prometheus for metrics
   - Set up proper monitoring and alerting

## 8. Cleanup
```bash
# Delete resources
kubectl delete deployment python-app-deployment
kubectl delete service python-app-service
kubectl delete namespace python-app
```

This guide provides a basic but complete setup for deploying a Python application to Kubernetes. The configuration includes resource limits, health checks, and proper service exposure, which are essential for a production environment.
