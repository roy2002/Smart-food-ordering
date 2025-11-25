#!/bin/bash

# Build all Docker images for the microservices (Version 2)
# This creates images with v2 suffix to avoid conflicts with existing images

echo "================================"
echo "Building Docker Images (V2)"
echo "================================"

# Build API Gateway V2
echo "\n[1/6] Building API Gateway V2..."
cd api-gateway
docker build -t api-gateway-v2:latest .
cd ..

# Build User Service V2
echo "\n[2/6] Building User Service V2..."
cd user-service
docker build -t user-service-v2:latest .
cd ..

# Build Restaurant Service V2
echo "\n[3/6] Building Restaurant Service V2..."
cd restaurant-service
docker build -t restaurant-service-v2:latest .
cd ..

# Build Order Service V2
echo "\n[4/6] Building Order Service V2..."
cd order-service
# Generate gRPC code first
chmod +x generate_proto.sh
./generate_proto.sh
docker build -t order-service-v2:latest .
cd ..

# Build Recommendation Service V2
echo "\n[5/6] Building Recommendation Service V2..."
cd recommendation-service
docker build -t recommendation-service-v2:latest .
cd ..

# Build Payment Service V2
echo "\n[6/6] Building Payment Service V2..."
cd payment-service
docker build -t payment-service-v2:latest .
cd ..

echo "\n================================"
echo "✓ All V2 images built successfully!"
echo "================================"

# List built images
echo "\nBuilt V2 images:"
docker images | grep -E "api-gateway-v2|user-service-v2|restaurant-service-v2|order-service-v2|recommendation-service-v2|payment-service-v2"

echo "\nTo run with Docker Compose V2:"
echo "  docker-compose -f docker-compose-v2.yml up"
echo "\nTo deploy to Kubernetes V2:"
echo "  kubectl apply -f kubernetes/03-services-v2.yaml"

echo "\nOriginal images are still available:"
docker images | grep -E "api-gateway:|user-service:|restaurant-service:|order-service:|recommendation-service:|payment-service:" | grep -v v2
