#!/bin/bash

# Deploy V2 services to Kubernetes
# This deploys V2 services alongside existing V1 services

echo "================================"
echo "Deploying V2 to Kubernetes"
echo "================================"

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is not installed"
    exit 1
fi

# Check if namespace exists, create if not
echo "\n[1/3] Checking namespace..."
if ! kubectl get namespace food-ordering &> /dev/null; then
    echo "Creating namespace: food-ordering"
    kubectl create namespace food-ordering
else
    echo "Namespace 'food-ordering' already exists"
fi

# Deploy databases (can share with V1 or use separate)
echo "\n[2/3] Deploying databases (using existing)..."
echo "V2 services will use the same database infrastructure as V1"

# Deploy V2 microservices
echo "\n[3/3] Deploying V2 microservices..."
kubectl apply -f kubernetes/03-services-v2.yaml

echo "\n================================"
echo "✓ V2 Deployment Complete!"
echo "================================"

# Show deployment status
echo "\nV2 Deployments:"
kubectl get deployments -n food-ordering | grep v2

echo "\nV2 Services:"
kubectl get services -n food-ordering | grep v2

echo "\nV2 Pods:"
kubectl get pods -n food-ordering | grep v2

echo "\nOriginal (V1) deployments still running:"
kubectl get deployments -n food-ordering | grep -v v2 | grep -E "user-service|restaurant-service|order-service|recommendation-service|payment-service|api-gateway"

echo "\n================================"
echo "Access Information"
echo "================================"
echo "V2 API Gateway: http://<node-ip>:30001"
echo "V1 API Gateway: http://<node-ip>:30000"
echo "\nGet node IP with: kubectl get nodes -o wide"

echo "\nTo check V2 logs:"
echo "  kubectl logs -n food-ordering deployment/api-gateway-v2"
echo "  kubectl logs -n food-ordering deployment/user-service-v2"
echo "  etc..."

echo "\nTo remove V2 deployment:"
echo "  kubectl delete -f kubernetes/03-services-v2.yaml"
