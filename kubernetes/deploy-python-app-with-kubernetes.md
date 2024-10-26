# Deploying a FastAPI Python Application with Kubernetes: A Step-by-Step Guide

## 1. Sample FastAPI Application
First, let's create a simple FastAPI application to deploy.

**`app.py`**
```python
from fastapi import FastAPI
import uvicorn
import os

app = FastAPI(title="Kubernetes Demo API")

@app.get("/")
async def root():
    return {"message": "Hello from Kubernetes!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
```

**`requirements.txt`**
```
fastapi==0.109.0
uvicorn==0.27.0
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
ENV PORT=8000

# Expose port
EXPOSE 8000

# Run the application with Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 3. Build and Push Docker Image
```bash
# Build the Docker image
docker build -t your-registry/fastapi-k8s-app:v1 .

# Push to your container registry
docker push your-registry/fastapi-k8s-app:v1
```

## 4. Kubernetes Manifests

### Pod Definition
**`pod.yaml`**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: fastapi-app-pod
  labels:
    app: fastapi-app
spec:
  containers:
  - name: fastapi-app
    image: your-registry/fastapi-k8s-app:v1
    ports:
    - containerPort: 8000
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
  name: fastapi-app-deployment
  labels:
    app: fastapi-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi-app
  template:
    metadata:
      labels:
        app: fastapi-app
    spec:
      containers:
      - name: fastapi-app
        image: your-registry/fastapi-k8s-app:v1
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

### Service Manifest
**`service.yaml`**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-app-service
spec:
  selector:
    app: fastapi-app
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 5. Deployment Commands
Here are the commands to deploy your application to Kubernetes:

```bash
# Create namespace (optional)
kubectl create namespace fastapi-app

# Apply the namespace to current context (if created)
kubectl config set-context --current --namespace=fastapi-app

# Deploy the application
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# Verify deployment
kubectl get deployments
kubectl get pods
kubectl get services

# Check pod logs
kubectl logs -l app=fastapi-app

# Scale deployment (optional)
kubectl scale deployment fastapi-app-deployment --replicas=5

# Check deployment status
kubectl rollout status deployment/fastapi-app-deployment
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
kubectl set image deployment/fastapi-app-deployment fastapi-app=your-registry/fastapi-k8s-app:v2

# Rollback if needed
kubectl rollout undo deployment/fastapi-app-deployment
```

## 7. Best Practices

1. **Resource Management**
   - Always specify resource requests and limits
   - Monitor resource usage regularly
   - Use horizontal pod autoscaling for scalability

2. **Health Checks**
   - Implement both liveness and readiness probes
   - Set appropriate timing for probes
   - Use FastAPI's dedicated health check endpoint

3. **Security**
   - Use private container registries
   - Implement RBAC (Role-Based Access Control)
   - Keep container images up to date
   - Use FastAPI's built-in security features when needed

4. **Logging and Monitoring**
   - Implement structured logging
   - Use Prometheus for metrics
   - Set up proper monitoring and alerting
   - Utilize FastAPI's built-in request logging

5. **FastAPI Specific**
   - Enable API documentation at `/docs` and `/redoc`
   - Use Pydantic models for request/response validation
   - Implement proper exception handling
   - Configure CORS if needed

## 8. Cleanup
```bash
# Delete resources
kubectl delete deployment fastapi-app-deployment
kubectl delete service fastapi-app-service
kubectl delete namespace fastapi-app
```

This guide provides a basic but complete setup for deploying a FastAPI application to Kubernetes. The configuration includes resource limits, health checks, and proper service exposure, which are essential for a production environment. FastAPI provides additional benefits like automatic API documentation, better performance, and built-in type checking.
