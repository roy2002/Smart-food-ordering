# Setup and Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Docker Compose Deployment](#docker-compose-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Testing the Application](#testing-the-application)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- **Python 3.11+**: [Download](https://www.python.org/downloads/)
- **Docker Desktop**: [Download](https://www.docker.com/products/docker-desktop/)
- **Minikube**: [Installation Guide](https://minikube.sigs.k8s.io/docs/start/)
- **kubectl**: [Installation Guide](https://kubernetes.io/docs/tasks/tools/)
- **Git**: [Download](https://git-scm.com/downloads)

### System Requirements
- **CPU**: 4+ cores
- **RAM**: 8+ GB
- **Disk**: 20+ GB free space

---

## Local Development Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd smart-food-ordering-platform
```

### 2. Set Up Python Virtual Environment

For each service, you can run it locally:

```bash
# User Service
cd user-service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set Up Databases

**PostgreSQL** (for User, Restaurant, Order services):
```bash
# Using Docker
docker run -d \
  --name postgres-user \
  -e POSTGRES_DB=userdb \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:15

docker run -d \
  --name postgres-restaurant \
  -e POSTGRES_DB=restaurantdb \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -p 5433:5432 \
  postgres:15

docker run -d \
  --name postgres-order \
  -e POSTGRES_DB=orderdb \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -p 5434:5432 \
  postgres:15
```

**MongoDB** (for Recommendation service):
```bash
docker run -d \
  --name mongo-recommendation \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  -p 27017:27017 \
  mongo:6
```

**RabbitMQ** (for Payment service):
```bash
docker run -d \
  --name rabbitmq \
  -e RABBITMQ_DEFAULT_USER=admin \
  -e RABBITMQ_DEFAULT_PASS=password \
  -p 5672:5672 \
  -p 15672:15672 \
  rabbitmq:3-management
```

### 4. Generate gRPC Code for Order Service

```bash
cd order-service
chmod +x generate_proto.sh
./generate_proto.sh
cd ..
```

### 5. Run Services Individually

**Terminal 1 - User Service:**
```bash
cd user-service
python app.py
```

**Terminal 2 - Restaurant Service:**
```bash
cd restaurant-service
python app.py
```

**Terminal 3 - Order Service:**
```bash
cd order-service
python app.py
```

**Terminal 4 - Recommendation Service:**
```bash
cd recommendation-service
python app.py
```

**Terminal 5 - Payment Service:**
```bash
cd payment-service
python app.py
```

**Terminal 6 - API Gateway:**
```bash
cd api-gateway
python app.py
```

---

## Docker Compose Deployment

**Easiest way to run the entire application!**

### 1. Build and Start All Services

```bash
# Make sure you're in the project root directory
docker-compose up --build
```

### 2. Run in Detached Mode

```bash
docker-compose up -d
```

### 3. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f user-service
```

### 4. Stop Services

```bash
docker-compose down

# Remove volumes (clean database)
docker-compose down -v
```

### 5. Access Services

- **API Gateway**: http://localhost:8000
- **User Service**: http://localhost:5001
- **Restaurant Service**: http://localhost:5002
- **Order Service**: localhost:50051 (gRPC)
- **Recommendation Service**: http://localhost:5004/graphql
- **RabbitMQ Management**: http://localhost:15672 (admin/password)

---

## Kubernetes Deployment

### 1. Start Minikube

```bash
# Start with sufficient resources
minikube start --cpus=4 --memory=8192

# Verify status
minikube status
```

### 2. Build Docker Images

```bash
# Make scripts executable
chmod +x build-images.sh
chmod +x deploy-kubernetes.sh

# Build all images
./build-images.sh
```

### 3. Deploy to Kubernetes

```bash
# Deploy all services
./deploy-kubernetes.sh
```

**Or manually:**

```bash
# Configure Docker to use Minikube
eval $(minikube docker-env)

# Build images in Minikube
./build-images.sh

# Create namespace
kubectl create namespace food-ordering

# Apply manifests
kubectl apply -f kubernetes/01-databases.yaml
kubectl apply -f kubernetes/02-databases-extended.yaml
kubectl apply -f kubernetes/03-services.yaml
```

### 4. Check Deployment Status

```bash
# View all pods
kubectl get pods -n food-ordering

# View all services
kubectl get services -n food-ordering

# View deployments
kubectl get deployments -n food-ordering

# Describe a pod (for troubleshooting)
kubectl describe pod <pod-name> -n food-ordering
```

### 5. Access the Application

**Option 1: NodePort (Already configured)**
```bash
# Get Minikube IP
minikube ip

# Access API Gateway at:
# http://<minikube-ip>:30000
```

**Option 2: Port Forwarding**
```bash
# Forward API Gateway
kubectl port-forward -n food-ordering svc/api-gateway 8000:8000

# Access at: http://localhost:8000
```

**Option 3: Minikube Service**
```bash
minikube service api-gateway -n food-ordering
```

### 6. View Logs

```bash
# All pods
kubectl logs -n food-ordering --all-containers=true

# Specific service
kubectl logs -n food-ordering -l app=user-service -f

# Specific pod
kubectl logs -n food-ordering <pod-name> -f
```

### 7. Scale Services

```bash
# Scale user service to 3 replicas
kubectl scale deployment user-service -n food-ordering --replicas=3

# Check scaling
kubectl get pods -n food-ordering -l app=user-service
```

### 8. Clean Up

```bash
# Delete namespace (removes everything)
kubectl delete namespace food-ordering

# Or delete specific resources
kubectl delete -f kubernetes/
```

---

## Push to DockerHub (Optional)

### 1. Tag and Push Images

```bash
# Make script executable
chmod +x push-to-dockerhub.sh

# Push images (replace with your DockerHub username)
./push-to-dockerhub.sh <your-dockerhub-username>
```

### 2. Update Kubernetes Manifests

Edit `kubernetes/03-services.yaml` and replace:
```yaml
image: user-service:latest
imagePullPolicy: IfNotPresent
```

With:
```yaml
image: <your-dockerhub-username>/user-service:latest
imagePullPolicy: Always
```

### 3. Redeploy with DockerHub Images

```bash
kubectl apply -f kubernetes/03-services.yaml
```

---

## Testing the Application

### 1. Health Checks

```bash
# Check all services are healthy
curl http://localhost:8000/health
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5004/health
```

### 2. User Registration and Login

**Register a new user:**
```bash
curl -X POST http://localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "username": "johndoe",
    "password": "SecurePass123!",
    "full_name": "John Doe",
    "phone": "+1234567890",
    "address": "123 Main St"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'
```

Save the JWT token from the response.

### 3. Browse Restaurants

```bash
# List all restaurants
curl http://localhost:8000/api/restaurants

# Search by cuisine
curl "http://localhost:8000/api/restaurants?cuisine_type=Italian"

# Get restaurant menu
curl http://localhost:8000/api/restaurants/1/menu
```

### 4. Create an Order

```bash
# Replace <TOKEN> with your JWT token
curl -X POST http://localhost:8000/api/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "restaurant_id": "1",
    "items": "[{\"item_id\": 1, \"quantity\": 2}, {\"item_id\": 2, \"quantity\": 1}]",
    "total_amount": 40.97,
    "delivery_address": "123 Main St",
    "payment_method": "CARD"
  }'
```

Watch the Payment Service logs to see the Saga pattern in action!

### 5. Get Recommendations (GraphQL)

```bash
curl -X POST http://localhost:8000/api/recommendations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "query": "{ recommendations(user_id: 1, limit: 5, algorithm: \"collaborative\") { recommended_items { name category price_range } } }"
  }'
```

### 6. Monitor RabbitMQ

Access RabbitMQ Management UI:
- **Docker Compose**: http://localhost:15672
- **Kubernetes**: Use port-forward
  ```bash
  kubectl port-forward -n food-ordering svc/rabbitmq 15672:15672
  ```
- Login: `admin` / `password`

---

## Troubleshooting

### Docker Compose Issues

**Services won't start:**
```bash
# Check logs
docker-compose logs <service-name>

# Rebuild without cache
docker-compose build --no-cache
docker-compose up
```

**Database connection errors:**
```bash
# Wait for databases to be ready (30-60 seconds on first run)
# Check database containers
docker-compose ps

# Restart services
docker-compose restart user-service
```

### Kubernetes Issues

**Pods in CrashLoopBackOff:**
```bash
# Check pod logs
kubectl logs -n food-ordering <pod-name>

# Describe pod for events
kubectl describe pod -n food-ordering <pod-name>

# Delete and recreate pod
kubectl delete pod -n food-ordering <pod-name>
```

**Images not found:**
```bash
# Make sure Docker is using Minikube's daemon
eval $(minikube docker-env)

# Rebuild images
./build-images.sh

# Check images in Minikube
minikube ssh docker images
```

**Services not accessible:**
```bash
# Check service endpoints
kubectl get endpoints -n food-ordering

# Use port-forward instead of NodePort
kubectl port-forward -n food-ordering svc/api-gateway 8000:8000
```

**Database initialization slow:**
```bash
# Give databases more time (2-3 minutes)
kubectl wait --for=condition=ready pod -l app=postgres-user -n food-ordering --timeout=300s
```

### gRPC Issues

**Order service gRPC errors:**
```bash
# Regenerate proto files
cd order-service
./generate_proto.sh
```

**Copy generated files to API Gateway:**
```bash
cp order-service/order_pb2.py api-gateway/proto/
cp order-service/order_pb2_grpc.py api-gateway/proto/
```

### General Tips

1. **Check all dependencies are running** before starting services
2. **Use health check endpoints** to verify service status
3. **Check firewall/antivirus** if ports are blocked
4. **Ensure sufficient system resources** (CPU, RAM, Disk)
5. **Review logs systematically** from databases → services → gateway

---

## Next Steps

1. **Explore the APIs** using the OpenAPI docs in `/architecture/openapi/`
2. **Test the GraphQL** playground at http://localhost:5004/graphql
3. **Monitor message flow** in RabbitMQ Management UI
4. **Scale services** in Kubernetes and observe load balancing
5. **Add more features** like real-time notifications, caching, etc.

---

## Support

For issues or questions:
1. Check the architecture documentation in `/architecture/`
2. Review service-specific README files
3. Check logs for error messages
4. Verify all prerequisites are installed

Happy coding! 🚀
