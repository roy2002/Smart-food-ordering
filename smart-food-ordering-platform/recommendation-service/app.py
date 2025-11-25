"""
Recommendation Service - GraphQL API
AI-powered food recommendations using collaborative filtering
Uses MongoDB for flexible schema and quick reads
"""

from flask import Flask
from flask_cors import CORS
import strawberry
from strawberry.flask.views import GraphQLView
from pymongo import MongoClient
from typing import List, Optional
import os
from datetime import datetime
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
CORS(app)

# MongoDB configuration
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://admin:password@localhost:27017/')
MONGO_DB = os.getenv('MONGO_DB', 'recommendationdb')

# MongoDB client
client = MongoClient(MONGO_URL)
db = client[MONGO_DB]

# Collections
users_collection = db['users']
items_collection = db['items']
interactions_collection = db['interactions']
recommendations_collection = db['recommendations']

# Seed sample data
def seed_data():
    """Seed initial recommendation data"""
    try:
        # Check if data exists
        if items_collection.count_documents({}) > 0:
            return
        
        # Sample food items
        items = [
            {
                'item_id': 1,
                'name': 'Margherita Pizza',
                'category': 'Italian',
                'type': 'Main Course',
                'features': ['cheese', 'tomato', 'basil', 'vegetarian'],
                'price_range': 'medium',
                'calories': 800,
                'is_vegetarian': True,
                'is_vegan': False
            },
            {
                'item_id': 2,
                'name': 'Pepperoni Pizza',
                'category': 'Italian',
                'type': 'Main Course',
                'features': ['cheese', 'tomato', 'pepperoni', 'meat'],
                'price_range': 'medium',
                'calories': 950,
                'is_vegetarian': False,
                'is_vegan': False
            },
            {
                'item_id': 3,
                'name': 'Kung Pao Chicken',
                'category': 'Chinese',
                'type': 'Main Course',
                'features': ['chicken', 'spicy', 'peanuts', 'meat'],
                'price_range': 'medium',
                'calories': 750,
                'is_vegetarian': False,
                'is_vegan': False
            },
            {
                'item_id': 4,
                'name': 'Vegetable Spring Rolls',
                'category': 'Chinese',
                'type': 'Appetizer',
                'features': ['vegetables', 'crispy', 'vegetarian'],
                'price_range': 'low',
                'calories': 300,
                'is_vegetarian': True,
                'is_vegan': True
            },
            {
                'item_id': 5,
                'name': 'Classic Burger',
                'category': 'American',
                'type': 'Main Course',
                'features': ['beef', 'cheese', 'lettuce', 'tomato', 'meat'],
                'price_range': 'medium',
                'calories': 850,
                'is_vegetarian': False,
                'is_vegan': False
            },
            {
                'item_id': 6,
                'name': 'Caesar Salad',
                'category': 'American',
                'type': 'Appetizer',
                'features': ['lettuce', 'caesar_dressing', 'croutons', 'vegetarian'],
                'price_range': 'low',
                'calories': 350,
                'is_vegetarian': True,
                'is_vegan': False
            }
        ]
        
        items_collection.insert_many(items)
        
        # Sample user preferences
        user_prefs = [
            {
                'user_id': 1,
                'preferences': {
                    'categories': ['Italian', 'American'],
                    'dietary': ['vegetarian'],
                    'price_range': 'medium'
                }
            },
            {
                'user_id': 2,
                'preferences': {
                    'categories': ['Chinese', 'Italian'],
                    'dietary': [],
                    'price_range': 'medium'
                }
            }
        ]
        
        users_collection.insert_many(user_prefs)
        
        # Sample interactions (user-item ratings)
        interactions = [
            {'user_id': 1, 'item_id': 1, 'rating': 5, 'timestamp': datetime.utcnow()},
            {'user_id': 1, 'item_id': 6, 'rating': 4, 'timestamp': datetime.utcnow()},
            {'user_id': 2, 'item_id': 2, 'rating': 5, 'timestamp': datetime.utcnow()},
            {'user_id': 2, 'item_id': 3, 'rating': 4, 'timestamp': datetime.utcnow()},
        ]
        
        interactions_collection.insert_many(interactions)
        print("Recommendation data seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding data: {str(e)}")

seed_data()

# GraphQL Types
@strawberry.type
class FoodItem:
    item_id: int
    name: str
    category: str
    type: str
    features: List[str]
    price_range: str
    calories: int
    is_vegetarian: bool
    is_vegan: bool
    recommendation_score: Optional[float] = None

@strawberry.type
class Recommendation:
    user_id: int
    recommended_items: List[FoodItem]
    timestamp: str
    algorithm: str

@strawberry.type
class SimilarItem:
    item: FoodItem
    similarity_score: float

# AI Recommendation Engine
class RecommendationEngine:
    
    @staticmethod
    def get_collaborative_recommendations(user_id: int, limit: int = 5) -> List[dict]:
        """
        Collaborative filtering recommendations
        Based on users with similar preferences
        """
        # Get user's interactions
        user_interactions = list(interactions_collection.find({'user_id': user_id}))
        
        if not user_interactions:
            # Return popular items for new users
            return RecommendationEngine.get_popular_items(limit)
        
        # Get all items user has interacted with
        interacted_items = {i['item_id'] for i in user_interactions}
        
        # Find similar users
        all_interactions = list(interactions_collection.find())
        user_item_matrix = {}
        
        for interaction in all_interactions:
            uid = interaction['user_id']
            iid = interaction['item_id']
            rating = interaction['rating']
            
            if uid not in user_item_matrix:
                user_item_matrix[uid] = {}
            user_item_matrix[uid][iid] = rating
        
        # Calculate user similarity
        if user_id not in user_item_matrix:
            return RecommendationEngine.get_popular_items(limit)
        
        current_user_items = user_item_matrix[user_id]
        
        # Find items liked by similar users
        recommended_items = {}
        for other_user, other_items in user_item_matrix.items():
            if other_user == user_id:
                continue
            
            # Calculate overlap
            common_items = set(current_user_items.keys()) & set(other_items.keys())
            if len(common_items) >= 1:  # At least one common item
                # Recommend items they liked but current user hasn't tried
                for item_id, rating in other_items.items():
                    if item_id not in interacted_items and rating >= 4:
                        recommended_items[item_id] = recommended_items.get(item_id, 0) + rating
        
        # Sort by score
        sorted_items = sorted(recommended_items.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        # Fetch item details
        recommendations = []
        for item_id, score in sorted_items:
            item = items_collection.find_one({'item_id': item_id})
            if item:
                item['recommendation_score'] = float(score)
                recommendations.append(item)
        
        if not recommendations:
            return RecommendationEngine.get_popular_items(limit)
        
        return recommendations
    
    @staticmethod
    def get_content_based_recommendations(user_id: int, limit: int = 5) -> List[dict]:
        """
        Content-based recommendations
        Based on item features and user preferences
        """
        # Get user preferences
        user = users_collection.find_one({'user_id': user_id})
        
        if not user or 'preferences' not in user:
            return RecommendationEngine.get_popular_items(limit)
        
        preferences = user['preferences']
        preferred_categories = preferences.get('categories', [])
        dietary_requirements = preferences.get('dietary', [])
        
        # Build query
        query = {}
        if preferred_categories:
            query['category'] = {'$in': preferred_categories}
        
        if 'vegetarian' in dietary_requirements:
            query['is_vegetarian'] = True
        if 'vegan' in dietary_requirements:
            query['is_vegan'] = True
        
        # Fetch matching items
        items = list(items_collection.find(query).limit(limit))
        
        if not items:
            return RecommendationEngine.get_popular_items(limit)
        
        return items
    
    @staticmethod
    def get_popular_items(limit: int = 5) -> List[dict]:
        """Get popular items based on interaction count"""
        pipeline = [
            {
                '$group': {
                    '_id': '$item_id',
                    'avg_rating': {'$avg': '$rating'},
                    'count': {'$sum': 1}
                }
            },
            {
                '$sort': {'avg_rating': -1, 'count': -1}
            },
            {
                '$limit': limit
            }
        ]
        
        popular_stats = list(interactions_collection.aggregate(pipeline))
        
        if not popular_stats:
            # Fallback to any items
            return list(items_collection.find().limit(limit))
        
        # Create a map of item_id to score
        score_map = {p['_id']: p['avg_rating'] * p['count'] for p in popular_stats}
        popular_item_ids = [p['_id'] for p in popular_stats]
        
        items = list(items_collection.find({'item_id': {'$in': popular_item_ids}}))
        
        # Add recommendation scores
        for item in items:
            item['recommendation_score'] = float(score_map.get(item['item_id'], 0.0))
        
        return items
    
    @staticmethod
    def get_similar_items(item_id: int, limit: int = 5) -> List[dict]:
        """
        Find similar items based on features
        Uses cosine similarity
        """
        target_item = items_collection.find_one({'item_id': item_id})
        
        if not target_item:
            return []
        
        target_features = set(target_item.get('features', []))
        all_items = list(items_collection.find({'item_id': {'$ne': item_id}}))
        
        similarities = []
        for item in all_items:
            item_features = set(item.get('features', []))
            
            # Calculate Jaccard similarity
            if len(target_features) == 0 and len(item_features) == 0:
                similarity = 0
            else:
                intersection = len(target_features & item_features)
                union = len(target_features | item_features)
                similarity = intersection / union if union > 0 else 0
            
            # Boost similarity if same category
            if item['category'] == target_item['category']:
                similarity += 0.2
            
            item['similarity_score'] = similarity
            similarities.append(item)
        
        # Sort by similarity
        similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return similarities[:limit]

# GraphQL Queries
@strawberry.type
class Query:
    
    @strawberry.field
    def recommendations(self, user_id: int, limit: int = 5, algorithm: str = "collaborative") -> Recommendation:
        """
        Get personalized recommendations for a user
        Algorithms: 'collaborative', 'content', 'hybrid'
        """
        if algorithm == "collaborative":
            items = RecommendationEngine.get_collaborative_recommendations(user_id, limit)
        elif algorithm == "content":
            items = RecommendationEngine.get_content_based_recommendations(user_id, limit)
        else:  # hybrid
            collab = RecommendationEngine.get_collaborative_recommendations(user_id, limit // 2)
            content = RecommendationEngine.get_content_based_recommendations(user_id, limit // 2)
            items = collab + content
        
        food_items = []
        for item in items:
            food_items.append(FoodItem(
                item_id=item['item_id'],
                name=item['name'],
                category=item['category'],
                type=item['type'],
                features=item.get('features', []),
                price_range=item['price_range'],
                calories=item['calories'],
                is_vegetarian=item['is_vegetarian'],
                is_vegan=item['is_vegan'],
                recommendation_score=item.get('recommendation_score')
            ))
        
        return Recommendation(
            user_id=user_id,
            recommended_items=food_items,
            timestamp=datetime.utcnow().isoformat(),
            algorithm=algorithm
        )
    
    @strawberry.field
    def similar_items(self, item_id: int, limit: int = 5) -> List[SimilarItem]:
        """Get items similar to the given item"""
        similar = RecommendationEngine.get_similar_items(item_id, limit)
        
        result = []
        for item in similar:
            result.append(SimilarItem(
                item=FoodItem(
                    item_id=item['item_id'],
                    name=item['name'],
                    category=item['category'],
                    type=item['type'],
                    features=item.get('features', []),
                    price_range=item['price_range'],
                    calories=item['calories'],
                    is_vegetarian=item['is_vegetarian'],
                    is_vegan=item['is_vegan']
                ),
                similarity_score=item.get('similarity_score', 0.0)
            ))
        
        return result
    
    @strawberry.field
    def search_items(self, 
                     category: Optional[str] = None,
                     is_vegetarian: Optional[bool] = None,
                     is_vegan: Optional[bool] = None,
                     max_calories: Optional[int] = None) -> List[FoodItem]:
        """Search and filter food items"""
        query = {}
        
        if category:
            query['category'] = category
        if is_vegetarian is not None:
            query['is_vegetarian'] = is_vegetarian
        if is_vegan is not None:
            query['is_vegan'] = is_vegan
        if max_calories:
            query['calories'] = {'$lte': max_calories}
        
        items = list(items_collection.find(query))
        
        return [FoodItem(
            item_id=item['item_id'],
            name=item['name'],
            category=item['category'],
            type=item['type'],
            features=item.get('features', []),
            price_range=item['price_range'],
            calories=item['calories'],
            is_vegetarian=item['is_vegetarian'],
            is_vegan=item['is_vegan']
        ) for item in items]

# Create GraphQL schema
schema = strawberry.Schema(query=Query)

# Health check route
@app.route('/health', methods=['GET'])
def health_check():
    from flask import jsonify
    return jsonify({'status': 'healthy', 'service': 'recommendation-service'}), 200

# Add GraphQL endpoint
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view('graphql_view', schema=schema)
)

if __name__ == '__main__':
    print("Starting Recommendation Service (GraphQL) on port 5004...")
    print(f"MongoDB: {MONGO_URL}")
    print(f"GraphQL endpoint: http://localhost:5004/graphql")
    app.run(host='0.0.0.0', port=5004, debug=True)
