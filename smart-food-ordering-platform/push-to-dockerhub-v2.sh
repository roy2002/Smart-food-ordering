#!/bin/bash

# Push Docker images V2 to DockerHub
# Usage: ./push-to-dockerhub-v2.sh <your-dockerhub-username>

if [ -z "$1" ]; then
    echo "Error: DockerHub username required"
    echo "Usage: ./push-to-dockerhub-v2.sh <dockerhub-username>"
    exit 1
fi

DOCKERHUB_USERNAME=$1

echo "================================"
echo "Pushing V2 Images to DockerHub"
echo "Username: $DOCKERHUB_USERNAME"
echo "================================"

# Login to DockerHub
echo "\nLogging in to DockerHub..."
docker login

# List of services with v2 suffix
SERVICES=("api-gateway-v2" "user-service-v2" "restaurant-service-v2" "order-service-v2" "recommendation-service-v2" "payment-service-v2")

# Tag and push each service
for SERVICE in "${SERVICES[@]}"; do
    echo "\n[Processing $SERVICE]"
    
    # Tag image
    echo "  Tagging ${SERVICE}:latest as ${DOCKERHUB_USERNAME}/${SERVICE}:latest"
    docker tag ${SERVICE}:latest ${DOCKERHUB_USERNAME}/${SERVICE}:latest
    docker tag ${SERVICE}:latest ${DOCKERHUB_USERNAME}/${SERVICE}:v2.0.0
    
    # Push latest tag
    echo "  Pushing ${DOCKERHUB_USERNAME}/${SERVICE}:latest"
    docker push ${DOCKERHUB_USERNAME}/${SERVICE}:latest
    
    # Push version tag
    echo "  Pushing ${DOCKERHUB_USERNAME}/${SERVICE}:v2.0.0"
    docker push ${DOCKERHUB_USERNAME}/${SERVICE}:v2.0.0
done

echo "\n================================"
echo "✓ All V2 images pushed successfully!"
echo "================================"

echo "\nPushed V2 images:"
for SERVICE in "${SERVICES[@]}"; do
    echo "  - ${DOCKERHUB_USERNAME}/${SERVICE}:latest"
    echo "  - ${DOCKERHUB_USERNAME}/${SERVICE}:v2.0.0"
done

echo "\nTo use these images in Kubernetes, update kubernetes/03-services-v2.yaml:"
echo "  Replace 'image: <service>-v2:latest' with 'image: ${DOCKERHUB_USERNAME}/<service>-v2:latest'"
echo "  And set 'imagePullPolicy: Always'"

echo "\nDockerHub Repository URLs:"
for SERVICE in "${SERVICES[@]}"; do
    echo "  https://hub.docker.com/r/${DOCKERHUB_USERNAME}/${SERVICE}"
done

echo "\n================================"
echo "NOTE: Original images remain unchanged"
echo "================================"
