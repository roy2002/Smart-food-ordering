#!/bin/bash

# Push Docker images to DockerHub
# Usage: ./push-to-dockerhub.sh <your-dockerhub-username>

if [ -z "$1" ]; then
    echo "Error: DockerHub username required"
    echo "Usage: ./push-to-dockerhub.sh <dockerhub-username>"
    exit 1
fi

DOCKERHUB_USERNAME=$1

echo "================================"
echo "Pushing Images to DockerHub"
echo "Username: $DOCKERHUB_USERNAME"
echo "================================"

# Login to DockerHub
echo "\nLogging in to DockerHub..."
docker login

# List of services
SERVICES=("api-gateway" "user-service" "restaurant-service" "order-service" "recommendation-service" "payment-service")

# Tag and push each service
for SERVICE in "${SERVICES[@]}"; do
    echo "\n[Processing $SERVICE]"
    
    # Tag image
    echo "  Tagging ${SERVICE}:latest as ${DOCKERHUB_USERNAME}/${SERVICE}:latest"
    docker tag ${SERVICE}:latest ${DOCKERHUB_USERNAME}/${SERVICE}:latest
    docker tag ${SERVICE}:latest ${DOCKERHUB_USERNAME}/${SERVICE}:v1.0.0
    
    # Push latest tag
    echo "  Pushing ${DOCKERHUB_USERNAME}/${SERVICE}:latest"
    docker push ${DOCKERHUB_USERNAME}/${SERVICE}:latest
    
    # Push version tag
    echo "  Pushing ${DOCKERHUB_USERNAME}/${SERVICE}:v1.0.0"
    docker push ${DOCKERHUB_USERNAME}/${SERVICE}:v1.0.0
done

echo "\n================================"
echo "✓ All images pushed successfully!"
echo "================================"

echo "\nPushed images:"
for SERVICE in "${SERVICES[@]}"; do
    echo "  - ${DOCKERHUB_USERNAME}/${SERVICE}:latest"
    echo "  - ${DOCKERHUB_USERNAME}/${SERVICE}:v1.0.0"
done

echo "\nTo use these images in Kubernetes, update kubernetes/03-services.yaml:"
echo "  Replace 'image: <service>:latest' with 'image: ${DOCKERHUB_USERNAME}/<service>:latest'"
echo "  And set 'imagePullPolicy: Always'"

echo "\nDockerHub Repository URLs:"
for SERVICE in "${SERVICES[@]}"; do
    echo "  https://hub.docker.com/r/${DOCKERHUB_USERNAME}/${SERVICE}"
done
