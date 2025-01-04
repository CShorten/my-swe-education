```bash
# Build and push worker image
docker build -f docker/worker.Dockerfile -t your-registry/temporal-worker:latest .
docker push your-registry/temporal-worker:latest

# Build and push orchestrator image
docker build -f docker/orchestrator.Dockerfile -t your-registry/temporal-orchestrator:latest .
docker push your-registry/temporal-orchestrator:latest
```
