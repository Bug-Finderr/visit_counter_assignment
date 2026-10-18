# Visit Counter Service

A distributed visit counter service built with FastAPI and Redis, designed to efficiently track page visits with support for caching, sharding, and batching.

## Overview

This system implements a website visit counter with progressive improvements:

- Basic in-memory counter
- Redis-based persistence
- Application-level caching
- Write batching optimization
- Redis sharding for scalability

## Architecture

1. **FastAPI Application**: REST API for recording and retrieving visit counts
2. **Redis Instances**: Multiple Redis nodes for distributed storage
3. **Consistent Hashing**: Algorithm to distribute data evenly across Redis nodes
4. **Caching Layers**: Both application-level and Redis-based caching
5. **Batch Processing**: Optimized write operations to reduce Redis calls

## Setup Instructions

### Prerequisites

- Docker

### Installation & Running

```bash
# Clone the repository
git clone https://github.com/Bug-Finderr/visit_counter_assignment.git

# Start the application
docker-compose up --build

# The API will be available at http://localhost:8000
```

### Developer Tools (Optional)

- Install the "Redis for VS Code" extension by Redis.io to view Redis data directly within VS Code

## API Endpoints

```bash
# Check service health
curl --location 'http://localhost:8000/'

# Record a visit for page_id=123
curl --location --request POST 'http://localhost:8000/api/v1/counter/visit/123'

# Get visit count for page_id=123
curl --location 'http://localhost:8000/api/v1/counter/visits/123'
```

## Kubernetes Deployment (Helm)

The `chart/` directory packages the app and its two Redis shards for Kubernetes, tested on minikube.

```bash
minikube start --cni=calico --cpus=4 --memory=6g

kubectl apply -f k8s/namespace.yaml
kubectl -n visit-counter create secret generic visit-counter-redis \
  --from-literal=password="$(openssl rand -hex 24)"

helm install visit-counter chart -n visit-counter --set image.tag=<commit-sha> --wait
```

The image is built and pushed to `ghcr.io/bug-finderr/visit-counter` by commit SHA from CI, so `image.tag` is a real commit from a green run. Extra flags: `--set monitoring.enabled=true` (Prometheus + alerts), `--set tracing.enabled=true` (Jaeger), `--set ingress.enabled=true` (HTTPS). The optional pieces themselves (monitoring values, Jaeger, TLS secret setup) are in `k8s/`.

CI (`.github/workflows/ci.yml`) runs on every push: lint + tests + secret scan, then image build + CVE scan + push, then a kind cluster installs the chart with that exact image and runs a smoke test.

Alerts (in `chart/templates/monitoring.yaml`): more than 5% of visit requests failing for 5 minutes, p95 latency above 500ms for 10 minutes, or no pods ready for 5 minutes. The SLO behind them: under 0.5% failed requests and p95 under 100ms for the visit endpoints.

## Implementation Tasks

### Task 1: Basic Visit Counter (48500f)

**High-Level Design**: Simple in-memory counter with no persistence.

```bash
git checkout 48500f
docker-compose up --build
```

**Expected Behavior**: Visit counts are stored in memory. When retrieving counts, response shows `served_via: "in_memory"`.

<br/>

### Task 2: Counter Using Redis (9f4565)

**High-Level Design**: Counter data persisted in Redis for durability.

```bash
git checkout 9f4565
docker-compose up --build
```

**Expected Behavior**: Visit counts persist after server restarts. Response shows `served_via: "redis"`.

<br/>

### Task 3: Application Layer Caching (304a27)

**High-Level Design**: Adds application-level caching to reduce Redis reads.

```bash
git checkout 304a27
docker-compose up --build
```

**Expected Behavior**: First read request fetches from Redis (`served_via: "redis"`), but subsequent reads within 5 seconds use the cache (`served_via: "in_memory"`).

<br/>

### Task 4: Batched Write Requests (c99398)

**High-Level Design**: Accumulates writes in memory and periodically flushes to Redis.

```bash
git checkout c99398
docker-compose up --build
```

**Expected Behavior**: Visit records are buffered in memory and flushed to Redis either periodically (every 30 seconds) or when a read request is made. You can observe these updates in Redis using the VS Code extension.

<br/>

### Task 5: Redis Sharding for Scalability (794fe7)

**High-Level Design**: Uses consistent hashing to distribute data across multiple Redis instances.

```bash
git checkout 794fe7
docker-compose up --build
```

**Expected Behavior**: Visit counts are distributed across multiple Redis instances based on the page_id. Responses show which Redis instance served the data (e.g., `served_via: "redis1"` or `served_via: "redis2"`).

**Automated Testing**:

```bash
# Run the load tests and verify sharding functionality
docker-compose up -d redis1 redis2
pip install -r requirements-dev.txt
PYTEST_RUNNING=1 REDIS_NODES=redis://localhost:7070,redis://127.0.0.1:7071 pytest -v -m "not slow"
```

The automated tests verify consistent hashing functionality, key distribution, and system performance under load (including a heavy load test with 50,000 requests).

<br/>

## Credits

- The automated tests were written with help from GitHub Copilot
- This README was generated with help from GitHub Copilot
- [Medium: Consistent Hashing - Distributed Cache](https://medium.com/@souravdas08/consistent-hashing-implemenation-a00699f408df)
- [Arpit Bhayani: Consistent Hashing](https://arpitbhayani.me/blogs/consistent-hashing/)
- Stack Overflow references
- Official documentation for FastAPI and Redis
