# Architecture Documentation

## System Overview

The Smart Food Ordering Platform is a microservices-based application that enables users to browse restaurants, place orders, receive AI-powered recommendations, and process payments. The system is designed using modern microservices patterns for scalability, resilience, and maintainability.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Applications                      │
│                    (Web, Mobile, Desktop)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  API Gateway   │  ◄── API Gateway Pattern
                    │   (Port 8000)  │      - Request Routing
                    │                │      - Authentication
                    └────────┬───────┘      - Rate Limiting
                             │              - Circuit Breaker
                ┌────────────┼────────────┐
                │            │            │
        ┌───────▼──┐  ┌──────▼─────┐  ┌──▼────────┐
        │  User    │  │Restaurant  │  │  Order    │
        │ Service  │  │  Service   │  │ Service   │
        │  (REST)  │  │   (REST)   │  │  (gRPC)   │
        │Port 5001 │  │ Port 5002  │  │Port 50051 │
        └────┬─────┘  └─────┬──────┘  └─────┬─────┘
             │              │                │
        ┌────▼────┐    ┌────▼────┐     ┌────▼────┐
        │PostgreSQL│   │PostgreSQL│    │PostgreSQL│
        │  UserDB  │   │Restaurant│    │ OrderDB  │
        └──────────┘   │    DB    │    └────┬─────┘
                       └──────────┘         │
                                            │ Publishes Events
                                            ▼
        ┌──────────────┐            ┌──────────────┐
        │Recommendation│            │   RabbitMQ   │
        │   Service    │            │Message Broker│
        │  (GraphQL)   │            └──────┬───────┘
        │  Port 5004   │                   │
        └──────┬───────┘                   │ Consumes Events
               │                           ▼
          ┌────▼────┐              ┌──────────────┐
          │ MongoDB │              │   Payment    │
          │Recommend│              │   Service    │
          │   DB    │              │(Event-Driven)│
          └─────────┘              └──────────────┘

Database-per-Service Pattern: Each service has its own database
Saga Pattern: Order → Payment → Status Update workflow
```

## Service Decomposition

### Decomposition Strategy: Business Capability

We chose **Business Capability decomposition** because each service represents a distinct business function:

1. **User Management** - Authentication, authorization, profile management
2. **Restaurant Catalog** - Restaurant and menu data management
3. **Order Processing** - Order creation, tracking, lifecycle management
4. **Recommendations** - AI-based personalized suggestions
5. **Payment Processing** - Payment transactions and refunds

### Why Business Capability over Business Domain?

- Clear functional boundaries
- Easier to scale specific capabilities independently
- Natural alignment with business teams
- Reduces cross-service dependencies

## Communication Mechanisms

### 1. REST (User & Restaurant Services)
- **Protocol**: HTTP/HTTPS
- **Format**: JSON
- **Use Case**: CRUD operations, simple request-response
- **Benefits**: 
  - Widespread support
  - Easy to test and debug
  - Human-readable
- **OpenAPI**: Available in `/architecture/openapi/`

### 2. gRPC (Order Service)
- **Protocol**: HTTP/2
- **Format**: Protocol Buffers
- **Use Case**: High-performance order operations
- **Benefits**:
  - Strongly typed contracts
  - Binary serialization (faster)
  - Bidirectional streaming capability
- **Proto Files**: Available in `/order-service/proto/`

### 3. GraphQL (Recommendation Service)
- **Protocol**: HTTP
- **Format**: JSON
- **Use Case**: Flexible querying of recommendations
- **Benefits**:
  - Client specifies exact data needs
  - Single endpoint for all queries
  - Reduces over-fetching/under-fetching
- **Schema**: Available in GraphQL playground at `/graphql`

### 4. Message Broker - RabbitMQ (Payment Service)
- **Protocol**: AMQP
- **Pattern**: Publish-Subscribe
- **Use Case**: Asynchronous event processing
- **Benefits**:
  - Decoupled services
  - Reliable message delivery
  - Event-driven architecture
  - Implements Saga pattern

## Design Patterns

### 1. API Gateway Pattern

**Purpose**: Single entry point for all client requests

**Implementation**:
- Located at `/api-gateway`
- Routes requests to appropriate microservices
- Handles authentication and authorization
- Implements rate limiting
- Provides circuit breaker functionality

**Benefits for Scalability**:
- Horizontal scaling of gateway instances
- Load balancing across service instances
- Request caching and response aggregation
- Reduces client complexity

**Benefits for Resilience**:
- Circuit breaker prevents cascade failures
- Timeout handling
- Retry logic with exponential backoff
- Fallback responses when services are down

**Code Example**:
```python
# Circuit Breaker in API Gateway
class CircuitBreaker:
    def __init__(self, threshold=5, timeout=60):
        self.threshold = threshold
        self.timeout = timeout
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            raise Exception("Circuit breaker is OPEN")
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if self.failure_count >= self.threshold:
                self.state = 'OPEN'
            raise e
```

### 2. Database-per-Service Pattern

**Purpose**: Each microservice owns and manages its own database

**Implementation**:
- User Service → PostgreSQL (userdb)
- Restaurant Service → PostgreSQL (restaurantdb)
- Order Service → PostgreSQL (orderdb)
- Recommendation Service → MongoDB (recommendationdb)

**Benefits for Scalability**:
- Services can scale independently
- Freedom to choose optimal database technology per service
- No shared database bottleneck
- Easier to shard individual databases

**Benefits for Resilience**:
- Database failure affects only one service
- No cascading database locks
- Isolated schema changes
- Independent backup/recovery

**Trade-offs**:
- Data consistency challenges (addressed by Saga pattern)
- No ACID transactions across services
- Potential data duplication

### 3. Saga Pattern

**Purpose**: Manage distributed transactions across multiple services

**Implementation**: Choreography-based Saga for Order → Payment flow

**Workflow**:
1. Order Service creates order → publishes `order.created` event
2. Payment Service receives event → processes payment
3. If payment succeeds:
   - Publishes `payment.completed` event
   - Order Service updates status to CONFIRMED
4. If payment fails:
   - Publishes `payment.failed` event
   - Order Service cancels order (compensation)

**Benefits for Scalability**:
- Asynchronous processing
- No distributed locks
- Services can process at their own pace
- Natural load distribution

**Benefits for Resilience**:
- Automatic compensation on failure
- Eventual consistency
- Retry mechanisms
- Failure isolation

**Code Example**:
```python
# In Order Service
def CreateOrder(self, request, context):
    # Step 1: Create order
    new_order = Order(...)
    db.add(new_order)
    db.commit()
    
    # Step 2: Publish event for Saga
    message_publisher.publish_event('order.created', {
        'order_id': new_order.id,
        'total_amount': new_order.total_amount
    })

# In Payment Service
def on_order_created(self, ch, method, properties, body):
    order_data = json.loads(body)
    success = self.process_payment(order_data)
    
    if success:
        # Step 3: Payment succeeded
        self.publish_event('payment.completed', {...})
    else:
        # Compensation: Trigger order cancellation
        self.publish_event('payment.failed', {...})
```

## Data Flow Examples

### Example 1: User Places Order

```
1. Client → API Gateway: POST /api/orders
2. API Gateway → Order Service (gRPC): CreateOrder()
3. Order Service → PostgreSQL: INSERT order
4. Order Service → RabbitMQ: Publish 'order.created'
5. Payment Service ← RabbitMQ: Consume 'order.created'
6. Payment Service: Process payment
7. Payment Service → RabbitMQ: Publish 'payment.completed'
8. Order Service ← RabbitMQ: Consume 'payment.completed'
9. Order Service → PostgreSQL: UPDATE order status
10. API Gateway → Client: Order confirmation
```

### Example 2: Get Personalized Recommendations

```
1. Client → API Gateway: POST /api/recommendations (GraphQL query)
2. API Gateway → Recommendation Service: GraphQL query
3. Recommendation Service → MongoDB: Fetch user preferences
4. Recommendation Service: Run AI algorithm (collaborative filtering)
5. Recommendation Service → MongoDB: Fetch recommended items
6. Recommendation Service → API Gateway: Return recommendations
7. API Gateway → Client: Recommended food items
```

## Scalability Considerations

1. **Horizontal Scaling**: All services can scale independently
2. **Database Sharding**: Each service database can be sharded
3. **Caching**: Redis can be added for frequently accessed data
4. **CDN**: Static assets can be served via CDN
5. **Load Balancing**: Kubernetes handles internal load balancing

## Resilience Features

1. **Circuit Breakers**: Prevent cascade failures
2. **Timeouts**: All service calls have timeouts
3. **Retries**: Automatic retry with exponential backoff
4. **Health Checks**: All services expose /health endpoint
5. **Graceful Degradation**: Services can operate in degraded mode

## Security

1. **JWT Authentication**: Token-based auth via User Service
2. **API Gateway**: Central authentication point
3. **HTTPS**: All external communication encrypted
4. **Database Credentials**: Stored in Kubernetes secrets (production)
5. **Rate Limiting**: Prevents abuse

## Monitoring & Observability

**Future Enhancements**:
- Distributed tracing (Jaeger/Zipkin)
- Centralized logging (ELK Stack)
- Metrics collection (Prometheus + Grafana)
- Health dashboards

## Deployment Strategy

1. **Containerization**: Each service in Docker container
2. **Orchestration**: Kubernetes on Minikube
3. **CI/CD**: GitHub Actions (or similar) for automated deployment
4. **Image Registry**: DockerHub for container images
5. **Configuration**: Environment variables + ConfigMaps

## Technology Justification

| Service | Technology | Reason |
|---------|-----------|---------|
| User/Restaurant | PostgreSQL | ACID transactions, relational data |
| Order | PostgreSQL + gRPC | Strong consistency, high performance |
| Recommendation | MongoDB | Flexible schema, fast reads |
| Payment | RabbitMQ | Reliable async messaging |
| API Gateway | Flask | Lightweight, Python ecosystem |

## Future Enhancements

1. Service mesh (Istio) for advanced traffic management
2. Caching layer (Redis) for improved performance
3. Full-text search (Elasticsearch) for restaurants
4. Real-time order tracking (WebSockets)
5. Advanced ML models for recommendations (TensorFlow/PyTorch)
