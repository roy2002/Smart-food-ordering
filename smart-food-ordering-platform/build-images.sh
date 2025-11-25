#!/bin/bash

# Build all Docker images for the microservices

echo "================================"
echo "Building Docker Images"
echo "================================"

# Build API Gateway
echo "\n[1/6] Building API Gateway..."
cd api-gateway
docker build -t api-gateway:latest .
cd ..

# Build User Service
echo "\n[2/6] Building User Service..."
cd user-service
docker build -t user-service:latest .
cd ..

# Build Restaurant Service
echo "\n[3/6] Building Restaurant Service..."
cd restaurant-service
docker build -t restaurant-service:latest .
cd ..

# Build Order Service
echo "\n[4/6] Building Order Service..."
cd order-service
# Generate gRPC code first
chmod +x generate_proto.sh
./generate_proto.sh
docker build -t order-service:latest .
cd ..

# Build Recommendation Service
echo "\n[5/6] Building Recommendation Service..."
cd recommendation-service
docker build -t recommendation-service:latest .
cd ..

# Build Payment Service
echo "\n[6/6] Building Payment Service..."
cd payment-service
docker build -t payment-service:latest .
cd ..

echo "\n================================"
echo "✓ All images built successfully!"
echo "================================"

# List built images
echo "\nBuilt images:"
docker images | grep -E "api-gateway|user-service|restaurant-service|order-service|recommendation-service|payment-service"

echo "\nTo run with Docker Compose:"
echo "  docker-compose up"
echo "\nTo deploy to Kubernetes:"
echo "  ./deploy-kubernetes.sh"
