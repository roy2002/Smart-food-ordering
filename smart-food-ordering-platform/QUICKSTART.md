# Quick Start Guide

Get the Smart Food Ordering Platform up and running in 5 minutes!

## 🚀 Fastest Way: Docker Compose

### Step 1: Prerequisites
```bash
# Check if Docker is installed
docker --version
docker-compose --version
```

### Step 2: Clone and Run
```bash
# Navigate to project directory
cd smart-food-ordering-platform

# Start all services
docker-compose up --build
```

### Step 3: Wait for Services
Wait about 60-90 seconds for all services to initialize. You'll see:
- ✓ Databases starting
- ✓ Services connecting
- ✓ "Started on port..." messages

### Step 4: Test the Application
```bash
# In a new terminal, make the test script executable
chmod +x test-api.sh

# Run tests
./test-api.sh
```

**That's it! Your microservices are running! 🎉**

---

## 📋 What's Running?

| Service | URL | Description |
|---------|-----|-------------|
| API Gateway | http://localhost:8000 | Main entry point |
| User Service | http://localhost:5001 | User management |
| Restaurant Service | http://localhost:5002 | Restaurant catalog |
| Order Service | localhost:50051 | Order processing (gRPC) |
| Recommendation Service | http://localhost:5004/graphql | AI recommendations |
| RabbitMQ UI | http://localhost:15672 | Message broker (admin/password) |

---

## 🧪 Quick API Tests

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Register a User
```bash
curl -X POST http://localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com",
    "username": "demo",
    "password": "Demo123!",
    "full_name": "Demo User"
  }'
```

Save the `token` from the response!

### 3. Browse Restaurants
```bash
curl http://localhost:8000/api/restaurants
```

### 4. Get Menu
```bash
curl http://localhost:8000/api/restaurants/1/menu
```

### 5. Create Order
```bash
# Replace <TOKEN> with your actual token
curl -X POST http://localhost:8000/api/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "restaurant_id": "1",
    "items": "[{\"item_id\": 1, \"quantity\": 2}]",
    "total_amount": 25.98,
    "delivery_address": "123 Main St",
    "payment_method": "CARD"
  }'
```

### 6. Get Recommendations (GraphQL)
```bash
curl -X POST http://localhost:8000/api/recommendations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "query": "{ recommendations(user_id: 1) { recommended_items { name category } } }"
  }'
```

---

## 🐰 Watch the Saga Pattern in Action

1. Open RabbitMQ Management UI: http://localhost:15672
   - Login: `admin` / `password`

2. Navigate to **Queues** tab

3. Create an order (see step 5 above)

4. Watch the messages flow:
   - `order.created` event published
   - `payment_queue` receives message
   - `payment.completed` or `payment.failed` published
   - Order status updated

5. Check Payment Service logs:
```bash
docker-compose logs -f payment-service
```

You'll see:
- Order received
- Payment processing
- Success/failure
- Status update events

---

## 🎯 Testing Design Patterns

### API Gateway Pattern
```bash
# All requests go through gateway (port 8000)
# Gateway routes to individual services
curl http://localhost:8000/api/restaurants  # → Restaurant Service
curl http://localhost:8000/api/users/1      # → User Service
```

### Database-per-Service Pattern
```bash
# Each service has its own database
docker-compose exec postgres-user psql -U user -d userdb -c "\dt"
docker-compose exec postgres-restaurant psql -U user -d restaurantdb -c "\dt"
docker-compose exec postgres-order psql -U user -d orderdb -c "\dt"
```

### Saga Pattern
See "Watch the Saga Pattern in Action" above!

---

## 📊 View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f user-service
docker-compose logs -f payment-service
docker-compose logs -f order-service

# Last 100 lines
docker-compose logs --tail=100 api-gateway
```

---

## 🛑 Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

---

## 🚢 Deploy to Kubernetes

### Step 1: Start Minikube
```bash
minikube start --cpus=4 --memory=8192
```

### Step 2: Deploy
```bash
# Make script executable
chmod +x deploy-kubernetes.sh

# Deploy all services
./deploy-kubernetes.sh
```

### Step 3: Access API Gateway
```bash
# Get Minikube IP
minikube ip

# Access at: http://<minikube-ip>:30000

# Or use port-forward
kubectl port-forward -n food-ordering svc/api-gateway 8000:8000
```

### Step 4: Check Status
```bash
kubectl get pods -n food-ordering
kubectl get services -n food-ordering
```

---

## 📦 Push to DockerHub

```bash
# Make script executable
chmod +x push-to-dockerhub.sh

# Push images (replace with your username)
./push-to-dockerhub.sh your-dockerhub-username
```

Your images will be at:
- `docker.io/your-username/user-service:latest`
- `docker.io/your-username/restaurant-service:latest`
- etc.

---

## 🐛 Troubleshooting

### Services won't start?
```bash
# Check Docker is running
docker ps

# Restart Docker Desktop
# Then try again:
docker-compose up --build
```

### Port already in use?
```bash
# Find what's using the port
lsof -i :8000  # On Mac/Linux
netstat -ano | findstr :8000  # On Windows

# Stop the process or change ports in docker-compose.yml
```

### Database connection errors?
```bash
# Wait 60 seconds for databases to initialize
# Check database logs
docker-compose logs postgres-user
```

### gRPC errors?
```bash
# Regenerate proto files
cd order-service
./generate_proto.sh

# Rebuild
docker-compose up --build order-service
```

---

## 📚 Next Steps

1. **Explore the APIs**: Check `architecture/openapi/` for full API docs
2. **Try GraphQL**: Visit http://localhost:5004/graphql
3. **Monitor RabbitMQ**: Watch message flow at http://localhost:15672
4. **Scale Services**: Try scaling in Kubernetes
5. **Add Features**: Extend the services with your own features!

---

## 🎓 Assignment Checklist

- [x] 5 microservices running
- [x] REST, gRPC, GraphQL, Message Broker implemented
- [x] API Gateway pattern working
- [x] Database-per-service pattern implemented
- [x] Saga pattern for order→payment flow
- [x] Docker Compose deployment works
- [x] Kubernetes manifests ready
- [x] DockerHub push script ready

**You're ready to submit! 🎉**

---

## 💡 Tips

- **Save your JWT token** after registration - you'll need it for authenticated requests
- **Watch the payment logs** to see the Saga pattern compensation when payments fail
- **Use the test script** (`./test-api.sh`) to verify everything works
- **Check service health** before testing: `curl http://localhost:8000/health`

---

## 📞 Support

If something doesn't work:
1. Check logs: `docker-compose logs <service-name>`
2. Verify prerequisites are installed
3. Ensure ports 5001, 5002, 5004, 8000, 50051, 5672, 15672 are available
4. Try clean restart: `docker-compose down -v && docker-compose up --build`

Happy coding! 🚀
