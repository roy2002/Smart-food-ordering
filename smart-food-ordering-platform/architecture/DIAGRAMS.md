# Architecture Diagrams

## 1. System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        CLIENT APPLICATIONS                            │
│              (Web Browser, Mobile App, Desktop App)                   │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             │ HTTP/HTTPS
                             │
                    ┌────────▼────────┐
                    │                 │
                    │   API GATEWAY   │ ◄─── API Gateway Pattern
                    │   Port: 8000    │      • Request Routing
                    │                 │      • Authentication (JWT)
                    │   Patterns:     │      • Rate Limiting
                    │   - Circuit     │      • Circuit Breaker
                    │     Breaker     │      • Load Balancing
                    │   - Rate Limit  │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┬─────────────┐
            │                │                │             │
            │ REST           │ REST           │ gRPC        │ GraphQL
            │                │                │             │
      ┌─────▼─────┐    ┌────▼────┐     ┌────▼─────┐  ┌───▼──────┐
      │   User    │    │Restaurant│     │  Order   │  │Recommend │
      │  Service  │    │ Service  │     │ Service  │  │ Service  │
      │           │    │          │     │          │  │          │
      │ REST API  │    │REST API  │     │  gRPC    │  │ GraphQL  │
      │Port: 5001 │    │Port: 5002│     │Port:50051│  │Port: 5004│
      └─────┬─────┘    └────┬─────┘     └────┬─────┘  └────┬─────┘
            │               │                 │             │
            │               │                 │ Publishes   │
            │               │                 │ Events      │
     ┌──────▼──────┐ ┌─────▼──────┐   ┌──────▼──────┐ ┌───▼──────┐
     │ PostgreSQL  │ │ PostgreSQL │   │ PostgreSQL  │ │ MongoDB  │
     │             │ │            │   │             │ │          │
     │   userdb    │ │restaurant  │   │  orderdb    │ │recommend │
     │             │ │    db      │   │             │ │   db     │
     └─────────────┘ └────────────┘   └──────┬──────┘ └──────────┘
                                              │
        Database-per-Service Pattern ─────────┘
        • Loose Coupling
        • Independent Scaling                 │
        • Technology Choice                   │
        • Fault Isolation                     │
                                              │
                                     ┌────────▼────────┐
                                     │                 │
                                     │    RabbitMQ     │
                                     │ Message Broker  │
                                     │                 │
                                     │   Exchanges:    │
                                     │  order_events   │
                                     │                 │
                                     │   Queues:       │
                                     │ payment_queue   │
                                     └────────┬────────┘
                                              │
                                              │ AMQP
                                              │ Consumes Events
                                     ┌────────▼────────┐
                                     │                 │
                                     │    Payment      │
                                     │    Service      │
                                     │                 │
                                     │ Event-Driven    │
                                     │ Saga Pattern    │
                                     └─────────────────┘
```

## 2. Saga Pattern Flow

### Success Scenario

```
┌─────────┐         ┌──────────┐         ┌─────────┐         ┌──────────┐
│  Client │         │  Order   │         │RabbitMQ │         │ Payment  │
│         │         │ Service  │         │         │         │ Service  │
└────┬────┘         └────┬─────┘         └────┬────┘         └────┬─────┘
     │                   │                    │                   │
     │  1. Create Order  │                    │                   │
     ├──────────────────►│                    │                   │
     │                   │                    │                   │
     │                   │ 2. Save Order      │                   │
     │                   │    (status=PENDING)│                   │
     │                   ├───────────┐        │                   │
     │                   │           │        │                   │
     │                   │◄──────────┘        │                   │
     │                   │                    │                   │
     │  3. Order Created │                    │                   │
     │◄──────────────────┤                    │                   │
     │                   │                    │                   │
     │                   │ 4. Publish         │                   │
     │                   │    order.created   │                   │
     │                   ├───────────────────►│                   │
     │                   │                    │                   │
     │                   │                    │ 5. Deliver Event  │
     │                   │                    ├──────────────────►│
     │                   │                    │                   │
     │                   │                    │                   │
     │                   │                    │  6. Process       │
     │                   │                    │     Payment       │
     │                   │                    │                   ├───┐
     │                   │                    │                   │   │
     │                   │                    │                   │◄──┘
     │                   │                    │                   │
     │                   │                    │  7. Publish       │
     │                   │                    │     payment.      │
     │                   │                    │     completed     │
     │                   │                    │◄──────────────────┤
     │                   │                    │                   │
     │                   │ 8. Update Order    │                   │
     │                   │    (status=        │                   │
     │                   │     CONFIRMED)     │                   │
     │                   │◄───────────────────┤                   │
     │                   │                    │                   │
     │                   │                    │                   │
     ▼                   ▼                    ▼                   ▼
```

### Failure Scenario (Compensation)

```
┌─────────┐         ┌──────────┐         ┌─────────┐         ┌──────────┐
│  Client │         │  Order   │         │RabbitMQ │         │ Payment  │
│         │         │ Service  │         │         │         │ Service  │
└────┬────┘         └────┬─────┘         └────┬────┘         └────┬─────┘
     │                   │                    │                   │
     │  Steps 1-5 same as success scenario   │                   │
     │                   │                    │                   │
     │                   │                    │  6. Process       │
     │                   │                    │     Payment       │
     │                   │                    │     ❌ FAILED     │
     │                   │                    │                   ├───┐
     │                   │                    │                   │   │
     │                   │                    │                   │◄──┘
     │                   │                    │                   │
     │                   │                    │  7. Publish       │
     │                   │                    │     payment.failed│
     │                   │                    │◄──────────────────┤
     │                   │                    │                   │
     │                   │ 8. COMPENSATION    │                   │
     │                   │    Update Order    │                   │
     │                   │    (status=        │                   │
     │                   │     CANCELLED)     │                   │
     │                   │◄───────────────────┤                   │
     │                   │                    │                   │
     │  9. Order         │                    │                   │
     │     Cancelled     │                    │                   │
     │     Notification  │                    │                   │
     │◄──────────────────┤                    │                   │
     │                   │                    │                   │
     ▼                   ▼                    ▼                   ▼
```

## 3. Communication Patterns

```
┌─────────────────────────────────────────────────────────────┐
│                    Communication Patterns                    │
└─────────────────────────────────────────────────────────────┘

1. REST (Synchronous)
   Client ──HTTP POST──► Service
   Client ◄──JSON Response── Service
   
   Used by: User Service, Restaurant Service
   Benefits: Simple, widely supported, human-readable

2. gRPC (Synchronous)
   Client ──HTTP/2 + Protobuf──► Service
   Client ◄──Protobuf Response── Service
   
   Used by: Order Service
   Benefits: Fast, strongly-typed, efficient binary format

3. GraphQL (Synchronous)
   Client ──HTTP POST + Query──► Service
   Client ◄──JSON (exact fields)── Service
   
   Used by: Recommendation Service
   Benefits: Flexible queries, no over/under-fetching

4. Message Broker (Asynchronous)
   Publisher ──Event──► RabbitMQ ──Event──► Subscriber
   
   Used by: Order Service → Payment Service
   Benefits: Decoupled, reliable, scalable
```

## 4. Deployment Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster (Minikube)                  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   Namespace: food-ordering                  │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │ │
│  │  │   Pod       │  │   Pod       │  │   Pod       │        │ │
│  │  │             │  │             │  │             │        │ │
│  │  │ API Gateway │  │ API Gateway │  │User Service │        │ │
│  │  │             │  │             │  │             │        │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘        │ │
│  │         ▲                  ▲               ▲               │ │
│  │         └──────────────────┴───────────────┘               │ │
│  │                          │                                 │ │
│  │                 ┌────────▼────────┐                        │ │
│  │                 │  LoadBalancer   │                        │ │
│  │                 │   Service       │                        │ │
│  │                 │  (ClusterIP)    │                        │ │
│  │                 └────────┬────────┘                        │ │
│  │                          │                                 │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │            Persistent Volume Claims                   │ │ │
│  │  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐             │ │ │
│  │  │  │User  │  │Rest. │  │Order │  │Mongo │             │ │ │
│  │  │  │DB PVC│  │DB PVC│  │DB PVC│  │  PVC │             │ │ │
│  │  │  └──────┘  └──────┘  └──────┘  └──────┘             │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Ingress (NodePort): 30000 → API Gateway                        │
└──────────────────────────────────────────────────────────────────┘
```

## 5. Data Flow Example: Create Order

```
1. Client Request
   │
   ├─► POST /api/orders
   │   Headers: Authorization: Bearer <JWT>
   │   Body: { restaurant_id, items, total_amount }
   │
2. API Gateway
   │
   ├─► Validate JWT token
   ├─► Check rate limit
   ├─► Circuit breaker check
   │
3. Route to Order Service (gRPC)
   │
   ├─► CreateOrder gRPC call
   │   Proto: CreateOrderRequest
   │
4. Order Service
   │
   ├─► Save to PostgreSQL (orderdb)
   │   Status: PENDING
   │
5. Publish Event
   │
   ├─► RabbitMQ: order.created
   │   { order_id, total_amount, user_id }
   │
6. Payment Service (Async)
   │
   ├─► Consume order.created event
   ├─► Process payment
   │
7a. Payment Success          7b. Payment Failed
    │                            │
    ├─► Publish:                 ├─► Publish:
    │   payment.completed        │   payment.failed
    │                            │
8a. Order Service            8b. Order Service
    │                            │
    ├─► Update status:           ├─► Update status:
    │   CONFIRMED                │   CANCELLED
    │                            │
9. Client receives order confirmation
```

## 6. Circuit Breaker State Machine

```
┌──────────┐
│  CLOSED  │ ◄─── Normal operation, requests flow
└────┬─────┘
     │
     │ failure_count >= threshold
     │
     ▼
┌──────────┐
│   OPEN   │ ◄─── Requests fail fast, service unavailable
└────┬─────┘
     │
     │ timeout expired
     │
     ▼
┌──────────┐
│HALF_OPEN │ ◄─── Test if service recovered
└────┬─────┘
     │
     ├─► Success: → CLOSED
     └─► Failure: → OPEN
```

## 7. Scalability Strategy

```
                     Load Balancer
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
   │Gateway 1│      │Gateway 2│      │Gateway 3│
   └────┬────┘      └────┬────┘      └────┬────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
        ┌────────────────┼────────────────┬────────────┐
        │                │                │            │
   ┌────▼────┐      ┌───▼────┐     ┌────▼────┐  ┌────▼────┐
   │User Svc │      │Rest Svc│     │Order Svc│  │Rec. Svc │
   │   x3    │      │   x3   │     │   x3    │  │   x3    │
   └────┬────┘      └────┬───┘     └────┬────┘  └────┬────┘
        │                │               │            │
        │                │               │            │
   ┌────▼────┐      ┌───▼────┐     ┌───▼────┐  ┌────▼────┐
   │UserDB   │      │RestDB  │     │OrderDB │  │MongoDB  │
   │(Sharded)│      │(Sharded│     │(Shard) │  │(Sharded)│
   └─────────┘      └────────┘     └────────┘  └─────────┘
```

**Key**: All services can scale horizontally, databases can be sharded independently
