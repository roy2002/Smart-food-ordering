# GraphQL Schema - Recommendation Service

## Overview
The Recommendation Service uses GraphQL to provide flexible querying of AI-powered food recommendations.

**Endpoint**: `http://localhost:5004/graphql`

## Schema Definition

```graphql
type FoodItem {
  item_id: Int!
  name: String!
  category: String!
  type: String!
  features: [String!]!
  price_range: String!
  calories: Int!
  is_vegetarian: Boolean!
  is_vegan: Boolean!
  recommendation_score: Float
}

type Recommendation {
  user_id: Int!
  recommended_items: [FoodItem!]!
  timestamp: String!
  algorithm: String!
}

type SimilarItem {
  item: FoodItem!
  similarity_score: Float!
}

type Query {
  # Get personalized recommendations for a user
  recommendations(
    user_id: Int!
    limit: Int = 5
    algorithm: String = "collaborative"  # collaborative, content, hybrid
  ): Recommendation!

  # Get items similar to a given item
  similar_items(
    item_id: Int!
    limit: Int = 5
  ): [SimilarItem!]!

  # Search and filter food items
  search_items(
    category: String
    is_vegetarian: Boolean
    is_vegan: Boolean
    max_calories: Int
  ): [FoodItem!]!
}
```

## Query Examples

### 1. Get Personalized Recommendations

**Using Collaborative Filtering:**
```graphql
query {
  recommendations(user_id: 1, limit: 5, algorithm: "collaborative") {
    user_id
    algorithm
    timestamp
    recommended_items {
      item_id
      name
      category
      price_range
      calories
      is_vegetarian
      recommendation_score
    }
  }
}
```

**Using Content-Based Filtering:**
```graphql
query {
  recommendations(user_id: 1, limit: 5, algorithm: "content") {
    user_id
    algorithm
    recommended_items {
      name
      category
      features
    }
  }
}
```

**Using Hybrid Approach:**
```graphql
query {
  recommendations(user_id: 2, algorithm: "hybrid") {
    recommended_items {
      name
      category
      price_range
    }
  }
}
```

### 2. Get Similar Items

```graphql
query {
  similar_items(item_id: 1, limit: 3) {
    similarity_score
    item {
      item_id
      name
      category
      features
    }
  }
}
```

### 3. Search Items with Filters

**Find Vegetarian Items:**
```graphql
query {
  search_items(is_vegetarian: true) {
    name
    category
    calories
    price_range
  }
}
```

**Find Low-Calorie Vegan Items:**
```graphql
query {
  search_items(is_vegan: true, max_calories: 500) {
    name
    calories
    category
  }
}
```

**Find Italian Items:**
```graphql
query {
  search_items(category: "Italian") {
    name
    price_range
    is_vegetarian
  }
}
```

## Response Examples

### Recommendation Response
```json
{
  "data": {
    "recommendations": {
      "user_id": 1,
      "algorithm": "collaborative",
      "timestamp": "2025-11-23T10:30:00.123456",
      "recommended_items": [
        {
          "item_id": 2,
          "name": "Pepperoni Pizza",
          "category": "Italian",
          "price_range": "medium",
          "calories": 950,
          "is_vegetarian": false,
          "recommendation_score": 4.5
        },
        {
          "item_id": 5,
          "name": "Classic Burger",
          "category": "American",
          "price_range": "medium",
          "calories": 850,
          "is_vegetarian": false,
          "recommendation_score": 4.2
        }
      ]
    }
  }
}
```

### Similar Items Response
```json
{
  "data": {
    "similar_items": [
      {
        "similarity_score": 0.85,
        "item": {
          "item_id": 2,
          "name": "Pepperoni Pizza",
          "category": "Italian",
          "features": ["cheese", "tomato", "pepperoni", "meat"]
        }
      },
      {
        "similarity_score": 0.65,
        "item": {
          "item_id": 6,
          "name": "Caesar Salad",
          "category": "American",
          "features": ["lettuce", "caesar_dressing", "croutons", "vegetarian"]
        }
      }
    ]
  }
}
```

## AI Algorithms

### 1. Collaborative Filtering
- Finds users with similar preferences
- Recommends items liked by similar users
- Based on user-item interaction matrix

### 2. Content-Based Filtering
- Analyzes user preferences (categories, dietary requirements)
- Recommends items matching user profile
- Uses item features and metadata

### 3. Hybrid Approach
- Combines collaborative and content-based methods
- Provides diverse recommendations
- Balances personalization and discovery

## Feature Matching

The recommendation engine uses **Jaccard Similarity** for feature matching:

```
Similarity = |Features_A ∩ Features_B| / |Features_A ∪ Features_B|
```

Additional boost (+0.2) for items in the same category.

## Testing with cURL

```bash
# Get recommendations
curl -X POST http://localhost:5004/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ recommendations(user_id: 1, limit: 5) { recommended_items { name category } } }"
  }'

# Get similar items
curl -X POST http://localhost:5004/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ similar_items(item_id: 1) { similarity_score item { name } } }"
  }'
```

## Integration with API Gateway

The API Gateway forwards GraphQL queries to the Recommendation Service:

```bash
curl -X POST http://localhost:8000/api/recommendations \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ recommendations(user_id: 1) { recommended_items { name } } }"
  }'
```
