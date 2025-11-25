#!/bin/bash

# Deploy microservices to Minikube Kubernetes cluster

echo "================================"
echo "Deploying to Kubernetes"
echo "================================"

# Check if Minikube is running
if ! minikube status | grep -q "Running"; then
    echo "Starting Minikube..."
    minikube start --cpus=4 --memory=8192
else
    echo "✓ Minikube is already running"
fi

# Configure Docker to use Minikube's Docker daemon
echo "\nConfiguring Docker environment..."
eval $(minikube docker-env)

# Build images in Minikube's Docker
echo "\nBuilding images in Minikube..."
./build-images.sh

# Create namespace
echo "\nCreating namespace..."
kubectl create namespace food-ordering --dry-run=client -o yaml | kubectl apply -f -

# Apply Kubernetes manifests
echo "\nApplying Kubernetes manifests..."

echo "  [1/3] Deploying databases..."
kubectl apply -f kubernetes/01-databases.yaml
kubectl apply -f kubernetes/02-databases-extended.yaml

echo "  Waiting for databases to be ready..."
sleep 30

echo "  [2/3] Deploying microservices..."
kubectl apply -f kubernetes/03-services.yaml

echo "  [3/3] Waiting for all pods to be ready..."
kubectl wait --for=condition=ready pod --all -n food-ordering --timeout=300s

# Get service status
echo "\n================================"
echo "Deployment Status"
echo "================================"
kubectl get pods -n food-ordering
echo ""
kubectl get services -n food-ordering

# Get API Gateway URL
echo "\n================================"
echo "Access Information"
echo "================================"
MINIKUBE_IP=$(minikube ip)
echo "API Gateway URL: http://${MINIKUBE_IP}:30000"
echo "RabbitMQ Management: Use port-forward to access"
echo ""
echo "To access RabbitMQ Management UI:"
echo "  kubectl port-forward -n food-ordering svc/rabbitmq 15672:15672"
echo "  Then open: http://localhost:15672 (admin/password)"
echo ""
echo "To access services directly:"
echo "  kubectl port-forward -n food-ordering svc/api-gateway 8000:8000"
echo ""
echo "To view logs:"
echo "  kubectl logs -n food-ordering -l app=<service-name> -f"
echo ""
echo "To delete deployment:"
echo "  kubectl delete namespace food-ordering"

echo "\n✓ Deployment complete!"
