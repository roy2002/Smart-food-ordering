# Smart Food Ordering Platform - Microservices Architecture

## Problem Statement
Enable users to order food, get personalized AI-powered recommendations, track orders, manage restaurants, and handle payments efficiently.

## System Architecture

### Microservices (5 services)
1. **User Service** (REST) - User authentication, profiles, management
2. **Restaurant Service** (REST) - Restaurant data, menus, availability
3. **Order Service** (gRPC) - Order management, status tracking
4. **Recommendation Service** (GraphQL) - AI-powered food recommendations
5. **Payment Service** (Message Broker) - Payment processing, events

### Communication Mechanisms
- **REST**: User & Restaurant services
- **gRPC**: Order service (fast, typed communication)
- **GraphQL**: Recommendation service (flexible queries)
- **Message Broker (RabbitMQ)**: Payment events, order notifications

### Decomposition Strategy
**Business Capability Decomposition** - Each service represents a distinct business function:
- User management capability
- Restaurant catalog capability
- Order processing capability
- Recommendation engine capability
- Payment processing capability

### Design Patterns Applied
1. **API Gateway**: Central entry point for routing, authentication, rate limiting
2. **Database-per-Service**: Each service has its own database for loose coupling
3. **Saga Pattern**: Distributed transaction management (order → payment → notification)

## Tech Stack
- **Language**: Python 3.11+
- **REST**: Flask
- **gRPC**: grpcio
- **GraphQL**: Strawberry
- **Message Broker**: RabbitMQ (pika)
- **Databases**: PostgreSQL, MongoDB
- **Containerization**: Docker
- **Orchestration**: Kubernetes (Minikube)
- **AI/ML**: scikit-learn, TensorFlow (for recommendations)

## Project Structure
```
smart-food-ordering-platform/
├── api-gateway/              # API Gateway service
├── user-service/             # User management (REST)
├── restaurant-service/       # Restaurant catalog (REST)
├── order-service/            # Order processing (gRPC)
├── recommendation-service/   # AI recommendations (GraphQL)
├── payment-service/          # Payment processing (Message Broker)
├── kubernetes/               # K8s manifests
├── docker-compose.yml        # Local development
└── architecture/             # Architecture diagrams & schemas
```

## Setup Instructions

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Minikube
- kubectl

### Local Development
```bash
# Start all services with Docker Compose
docker-compose up --build

# Or run individual services
cd user-service && python app.py
cd restaurant-service && python app.py
# ... etc
```

### Kubernetes Deployment
```bash
# Start Minikube
minikube start

# Apply manifests
kubectl apply -f kubernetes/

# Check deployments
kubectl get pods
kubectl get services
```

## API Endpoints

### API Gateway
- Base URL: `http://localhost:8000`

### User Service (REST)
- POST `/api/users/register` - Register user
- POST `/api/users/login` - Login
- GET `/api/users/{id}` - Get user profile

### Restaurant Service (REST)
- GET `/api/restaurants` - List restaurants
- GET `/api/restaurants/{id}` - Get restaurant details
- GET `/api/restaurants/{id}/menu` - Get menu

### Order Service (gRPC)
- `CreateOrder` - Create new order
- `GetOrder` - Get order details
- `UpdateOrderStatus` - Update order status

### Recommendation Service (GraphQL)
- Query: `recommendations(userId: ID!)` - Get personalized recommendations
- Query: `similarItems(itemId: ID!)` - Get similar food items

### Payment Service (Message Broker)
- Listens to: `order.created` events
- Publishes: `payment.completed`, `payment.failed` events

## Design Pattern Explanations

### 1. API Gateway Pattern
- **Purpose**: Single entry point for all client requests
- **Benefits**: 
  - Centralized authentication & authorization
  - Request routing & load balancing
  - Rate limiting & throttling
  - Reduces client complexity
- **Scalability**: Horizontal scaling of gateway instances
- **Resilience**: Circuit breaker integration, timeout handling

### 2. Database-per-Service Pattern
- **Purpose**: Each service owns its database
- **Benefits**:
  - Loose coupling between services
  - Independent scaling & technology choice
  - Fault isolation
- **Scalability**: Services can scale independently
- **Resilience**: Database failure affects only one service

### 3. Saga Pattern
- **Purpose**: Manage distributed transactions
- **Implementation**: Order → Payment → Notification flow
- **Benefits**:
  - Maintains data consistency across services
  - Compensating transactions for rollback
  - Event-driven coordination
- **Scalability**: Async processing, no distributed locks
- **Resilience**: Automatic compensation on failure

## License
MIT
