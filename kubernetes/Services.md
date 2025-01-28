A Service in Kubernetes is an abstraction that defines a logical set of Pods and a policy to access them. Think of it as a reliable endpoint for a group of Pods that might come and go (due to scaling, failures, deployments, etc.).
The key types of Services are:

ClusterIP (default)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-internal-service
spec:
  selector:
    app: my-app
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
  type: ClusterIP
```

Only accessible within the cluster
Gets a stable internal IP address
Great for internal microservices communication

NodePort

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-nodeport-service
spec:
  type: NodePort
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 8080
      nodePort: 30007  # Optional: Kubernetes assigns one if not specified
```

Exposes the service on each Node's IP at a static port
Accessible from outside the cluster
Port range is typically 30000-32767
Less common in production due to security and port management challenges


LoadBalancer

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-loadbalancer
spec:
  type: LoadBalancer
  selector:
    app: my-app
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
```

Creates an external load balancer in supported cloud platforms
Automatically creates a NodePort and ClusterIP service as well
Most common for production services that need to be accessible from the internet


ExternalName

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-external-service
spec:
  type: ExternalName
  externalName: api.external-service.com
```

Maps the service to a DNS name
Used for accessing external services through internal DNS

Key concepts that apply to all Services:

Labels and Selectors: Services use these to know which Pods to route traffic to
Endpoints: Kubernetes automatically creates and maintains a list of all Pod IPs that match the Service's selector
Port mapping: Services can map their port to any target port in the Pod
Session Affinity: Can be configured to stick requests to specific Pods

Example of a complete Service with labels:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
  labels:
    app: web
    env: prod
spec:
  selector:
    app: web
    tier: frontend
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: 8080
  sessionAffinity: ClientIP
  type: ClusterIP
```

Services are fundamental to Kubernetes networking because they:

Provide stable endpoints for Pod-to-Pod communication
Handle Pod IP changes transparently
Offer basic load balancing
Enable service discovery through DNS
Allow for easy scaling of applications
