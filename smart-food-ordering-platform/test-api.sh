#!/bin/bash

# API Testing Script
# Tests all microservices and demonstrates functionality

BASE_URL="http://localhost:8000"
USER_SERVICE="http://localhost:5001"
RESTAURANT_SERVICE="http://localhost:5002"
RECOMMENDATION_SERVICE="http://localhost:5004"

echo "========================================="
echo "Smart Food Ordering Platform - API Tests"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local method=$3
    local data=$4
    local expected_code=$5
    
    echo -e "${BLUE}Testing: $name${NC}"
    
    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$url")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$url" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" == "$expected_code" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC} (Expected $expected_code, got $http_code)"
        ((FAILED++))
    fi
    
    echo "Response: $body"
    echo ""
}

# 1. Health Checks
echo "========================================="
echo "1. HEALTH CHECKS"
echo "========================================="
echo ""

test_endpoint "API Gateway Health" "$BASE_URL/health" "GET" "" "200"
test_endpoint "User Service Health" "$USER_SERVICE/health" "GET" "" "200"
test_endpoint "Restaurant Service Health" "$RESTAURANT_SERVICE/health" "GET" "" "200"
test_endpoint "Recommendation Service Health" "$RECOMMENDATION_SERVICE/health" "GET" "" "200"

# 2. User Service Tests (REST)
echo "========================================="
echo "2. USER SERVICE (REST API)"
echo "========================================="
echo ""

# Register user
USER_DATA='{
  "email": "testuser@example.com",
  "username": "testuser",
  "password": "SecurePass123!",
  "full_name": "Test User",
  "phone": "+1234567890",
  "address": "123 Test St"
}'

echo "Registering new user..."
response=$(curl -s -X POST "$BASE_URL/api/users/register" \
    -H "Content-Type: application/json" \
    -d "$USER_DATA")

echo "Response: $response"
TOKEN=$(echo $response | grep -o '"token":"[^"]*' | cut -d'"' -f4)
USER_ID=$(echo $response | grep -o '"id":[0-9]*' | cut -d':' -f2)

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✓ User registered successfully${NC}"
    echo "Token: $TOKEN"
    echo "User ID: $USER_ID"
    ((PASSED++))
else
    echo -e "${RED}✗ User registration failed${NC}"
    ((FAILED++))
fi
echo ""

# Login
LOGIN_DATA='{
  "email": "testuser@example.com",
  "password": "SecurePass123!"
}'

test_endpoint "User Login" "$BASE_URL/api/users/login" "POST" "$LOGIN_DATA" "200"

# Get user profile (with auth)
if [ -n "$TOKEN" ] && [ -n "$USER_ID" ]; then
    echo -e "${BLUE}Testing: Get User Profile${NC}"
    response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/users/$USER_ID" \
        -H "Authorization: Bearer $TOKEN")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" == "200" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code)"
        ((FAILED++))
    fi
    echo "Response: $body"
    echo ""
fi

# 3. Restaurant Service Tests (REST)
echo "========================================="
echo "3. RESTAURANT SERVICE (REST API)"
echo "========================================="
echo ""

test_endpoint "List All Restaurants" "$BASE_URL/api/restaurants" "GET" "" "200"
test_endpoint "Search Italian Restaurants" "$BASE_URL/api/restaurants?cuisine_type=Italian" "GET" "" "200"
test_endpoint "Get Restaurant Details" "$BASE_URL/api/restaurants/1" "GET" "" "200"
test_endpoint "Get Restaurant Menu" "$BASE_URL/api/restaurants/1/menu" "GET" "" "200"
test_endpoint "Filter Vegetarian Items" "$BASE_URL/api/restaurants/1/menu?vegetarian=true" "GET" "" "200"

# 4. Order Service Tests (gRPC via Gateway)
echo "========================================="
echo "4. ORDER SERVICE (gRPC)"
echo "========================================="
echo ""

if [ -n "$TOKEN" ]; then
    ORDER_DATA='{
      "restaurant_id": "1",
      "items": "[{\"item_id\": 1, \"name\": \"Margherita Pizza\", \"quantity\": 2, \"price\": 12.99}]",
      "total_amount": 25.98,
      "delivery_address": "123 Test St, City",
      "payment_method": "CARD"
    }'
    
    echo -e "${BLUE}Testing: Create Order${NC}"
    response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/orders" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d "$ORDER_DATA")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    ORDER_ID=$(echo $body | grep -o '"order_id":"[^"]*' | cut -d'"' -f4)
    
    if [ "$http_code" == "201" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        echo "Order ID: $ORDER_ID"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code)"
        ((FAILED++))
    fi
    echo "Response: $body"
    echo ""
    
    # Get order details
    if [ -n "$ORDER_ID" ]; then
        sleep 3  # Wait for order processing
        echo -e "${BLUE}Testing: Get Order Details${NC}"
        response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/orders/$ORDER_ID" \
            -H "Authorization: Bearer $TOKEN")
        
        http_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | sed '$d')
        
        if [ "$http_code" == "200" ]; then
            echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
            ((PASSED++))
        else
            echo -e "${RED}✗ FAILED${NC} (HTTP $http_code)"
            ((FAILED++))
        fi
        echo "Response: $body"
        echo ""
    fi
fi

# 5. Recommendation Service Tests (GraphQL)
echo "========================================="
echo "5. RECOMMENDATION SERVICE (GraphQL)"
echo "========================================="
echo ""

if [ -n "$TOKEN" ] && [ -n "$USER_ID" ]; then
    # Get recommendations
    GRAPHQL_QUERY='{
      "query": "{ recommendations(user_id: '$USER_ID', limit: 3, algorithm: \"collaborative\") { user_id algorithm recommended_items { name category price_range calories } } }"
    }'
    
    echo -e "${BLUE}Testing: Get Recommendations${NC}"
    response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/recommendations" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d "$GRAPHQL_QUERY")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" == "200" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code)"
        ((FAILED++))
    fi
    echo "Response: $body"
    echo ""
    
    # Get similar items
    SIMILAR_QUERY='{
      "query": "{ similar_items(item_id: 1, limit: 3) { similarity_score item { name category } } }"
    }'
    
    echo -e "${BLUE}Testing: Get Similar Items${NC}"
    response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/recommendations" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d "$SIMILAR_QUERY")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" == "200" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code)"
        ((FAILED++))
    fi
    echo "Response: $body"
    echo ""
fi

# Summary
echo "========================================="
echo "TEST SUMMARY"
echo "========================================="
echo -e "Total Tests: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
