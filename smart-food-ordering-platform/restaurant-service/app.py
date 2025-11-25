"""
Restaurant Service - REST API
Manages restaurant data, menus, and availability
Database-per-Service Pattern: Uses its own PostgreSQL database
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5433/restaurantdb')

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Restaurant Model
class Restaurant(Base):
    __tablename__ = 'restaurants'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    address = Column(String)
    phone = Column(String)
    email = Column(String)
    cuisine_type = Column(String)  # Italian, Chinese, Indian, etc.
    rating = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    opening_time = Column(String, default="09:00")
    closing_time = Column(String, default="22:00")
    delivery_fee = Column(Float, default=0.0)
    minimum_order = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    menu_items = relationship("MenuItem", back_populates="restaurant", cascade="all, delete-orphan")

# Menu Item Model
class MenuItem(Base):
    __tablename__ = 'menu_items'
    
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category = Column(String)  # Appetizer, Main Course, Dessert, Beverage
    is_vegetarian = Column(Boolean, default=False)
    is_vegan = Column(Boolean, default=False)
    is_available = Column(Boolean, default=True)
    image_url = Column(String)
    ingredients = Column(Text)
    calories = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    restaurant = relationship("Restaurant", back_populates="menu_items")

# Create tables
Base.metadata.create_all(bind=engine)

# Seed data function
def seed_data():
    """Seed initial restaurant data"""
    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(Restaurant).count() > 0:
            return
        
        # Create sample restaurants
        restaurants = [
            Restaurant(
                name="Pizza Paradise",
                description="Authentic Italian pizzas and pasta",
                address="123 Main St, City",
                phone="+1234567890",
                email="contact@pizzaparadise.com",
                cuisine_type="Italian",
                rating=4.5,
                delivery_fee=2.99,
                minimum_order=15.00
            ),
            Restaurant(
                name="Dragon Wok",
                description="Traditional Chinese cuisine",
                address="456 Oak Ave, City",
                phone="+1234567891",
                email="info@dragonwok.com",
                cuisine_type="Chinese",
                rating=4.3,
                delivery_fee=3.50,
                minimum_order=20.00
            ),
            Restaurant(
                name="Burger House",
                description="Gourmet burgers and fries",
                address="789 Elm St, City",
                phone="+1234567892",
                email="hello@burgerhouse.com",
                cuisine_type="American",
                rating=4.7,
                delivery_fee=2.50,
                minimum_order=10.00
            )
        ]
        
        for restaurant in restaurants:
            db.add(restaurant)
        
        db.commit()
        
        # Add menu items for Pizza Paradise
        pizza_restaurant = db.query(Restaurant).filter(Restaurant.name == "Pizza Paradise").first()
        menu_items = [
            MenuItem(
                restaurant_id=pizza_restaurant.id,
                name="Margherita Pizza",
                description="Classic pizza with tomato, mozzarella, and basil",
                price=12.99,
                category="Main Course",
                is_vegetarian=True,
                calories=800
            ),
            MenuItem(
                restaurant_id=pizza_restaurant.id,
                name="Pepperoni Pizza",
                description="Pepperoni and cheese on tomato sauce",
                price=14.99,
                category="Main Course",
                calories=950
            ),
            MenuItem(
                restaurant_id=pizza_restaurant.id,
                name="Caesar Salad",
                description="Fresh romaine lettuce with caesar dressing",
                price=8.99,
                category="Appetizer",
                is_vegetarian=True,
                calories=350
            )
        ]
        
        for item in menu_items:
            db.add(item)
        
        db.commit()
        print("Sample data seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding data: {str(e)}")
        db.rollback()
    finally:
        db.close()

# Seed data on startup
seed_data()

# Routes
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'restaurant-service'}), 200

@app.route('/api/restaurants', methods=['GET'])
def get_restaurants():
    """Get all restaurants with optional filtering"""
    db = SessionLocal()
    try:
        query = db.query(Restaurant).filter(Restaurant.is_active == True)
        
        # Filter by cuisine type
        cuisine_type = request.args.get('cuisine_type')
        if cuisine_type:
            query = query.filter(Restaurant.cuisine_type.ilike(f'%{cuisine_type}%'))
        
        # Filter by minimum rating
        min_rating = request.args.get('min_rating')
        if min_rating:
            query = query.filter(Restaurant.rating >= float(min_rating))
        
        # Search by name
        search = request.args.get('search')
        if search:
            query = query.filter(Restaurant.name.ilike(f'%{search}%'))
        
        restaurants = query.all()
        
        return jsonify({
            'restaurants': [{
                'id': r.id,
                'name': r.name,
                'description': r.description,
                'address': r.address,
                'cuisine_type': r.cuisine_type,
                'rating': r.rating,
                'delivery_fee': r.delivery_fee,
                'minimum_order': r.minimum_order,
                'opening_time': r.opening_time,
                'closing_time': r.closing_time
            } for r in restaurants]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch restaurants: {str(e)}'}), 500
    finally:
        db.close()

@app.route('/api/restaurants/<int:restaurant_id>', methods=['GET'])
def get_restaurant(restaurant_id):
    """Get restaurant details"""
    db = SessionLocal()
    try:
        restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        
        if not restaurant:
            return jsonify({'error': 'Restaurant not found'}), 404
        
        return jsonify({
            'id': restaurant.id,
            'name': restaurant.name,
            'description': restaurant.description,
            'address': restaurant.address,
            'phone': restaurant.phone,
            'email': restaurant.email,
            'cuisine_type': restaurant.cuisine_type,
            'rating': restaurant.rating,
            'delivery_fee': restaurant.delivery_fee,
            'minimum_order': restaurant.minimum_order,
            'opening_time': restaurant.opening_time,
            'closing_time': restaurant.closing_time,
            'is_active': restaurant.is_active
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch restaurant: {str(e)}'}), 500
    finally:
        db.close()

@app.route('/api/restaurants/<int:restaurant_id>/menu', methods=['GET'])
def get_restaurant_menu(restaurant_id):
    """Get restaurant menu items"""
    db = SessionLocal()
    try:
        restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        
        if not restaurant:
            return jsonify({'error': 'Restaurant not found'}), 404
        
        # Filter by category if provided
        category = request.args.get('category')
        query = db.query(MenuItem).filter(
            MenuItem.restaurant_id == restaurant_id,
            MenuItem.is_available == True
        )
        
        if category:
            query = query.filter(MenuItem.category == category)
        
        # Filter vegetarian/vegan
        if request.args.get('vegetarian') == 'true':
            query = query.filter(MenuItem.is_vegetarian == True)
        
        if request.args.get('vegan') == 'true':
            query = query.filter(MenuItem.is_vegan == True)
        
        menu_items = query.all()
        
        return jsonify({
            'restaurant_id': restaurant_id,
            'restaurant_name': restaurant.name,
            'menu_items': [{
                'id': item.id,
                'name': item.name,
                'description': item.description,
                'price': item.price,
                'category': item.category,
                'is_vegetarian': item.is_vegetarian,
                'is_vegan': item.is_vegan,
                'calories': item.calories,
                'image_url': item.image_url
            } for item in menu_items]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch menu: {str(e)}'}), 500
    finally:
        db.close()

@app.route('/api/restaurants', methods=['POST'])
def create_restaurant():
    """Create a new restaurant (admin only - simplified)"""
    data = request.json
    
    if not data.get('name'):
        return jsonify({'error': 'Restaurant name is required'}), 400
    
    db = SessionLocal()
    try:
        new_restaurant = Restaurant(
            name=data['name'],
            description=data.get('description', ''),
            address=data.get('address', ''),
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            cuisine_type=data.get('cuisine_type', ''),
            delivery_fee=data.get('delivery_fee', 0.0),
            minimum_order=data.get('minimum_order', 0.0)
        )
        
        db.add(new_restaurant)
        db.commit()
        db.refresh(new_restaurant)
        
        return jsonify({
            'message': 'Restaurant created successfully',
            'restaurant': {
                'id': new_restaurant.id,
                'name': new_restaurant.name,
                'cuisine_type': new_restaurant.cuisine_type
            }
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': f'Failed to create restaurant: {str(e)}'}), 500
    finally:
        db.close()

@app.route('/api/restaurants/<int:restaurant_id>/menu', methods=['POST'])
def add_menu_item(restaurant_id):
    """Add menu item to restaurant"""
    data = request.json
    
    if not data.get('name') or not data.get('price'):
        return jsonify({'error': 'Item name and price are required'}), 400
    
    db = SessionLocal()
    try:
        # Check if restaurant exists
        restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        if not restaurant:
            return jsonify({'error': 'Restaurant not found'}), 404
        
        new_item = MenuItem(
            restaurant_id=restaurant_id,
            name=data['name'],
            description=data.get('description', ''),
            price=float(data['price']),
            category=data.get('category', 'Main Course'),
            is_vegetarian=data.get('is_vegetarian', False),
            is_vegan=data.get('is_vegan', False),
            calories=data.get('calories')
        )
        
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        
        return jsonify({
            'message': 'Menu item added successfully',
            'item': {
                'id': new_item.id,
                'name': new_item.name,
                'price': new_item.price
            }
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': f'Failed to add menu item: {str(e)}'}), 500
    finally:
        db.close()

if __name__ == '__main__':
    print("Starting Restaurant Service on port 5002...")
    print(f"Database: {DATABASE_URL}")
    app.run(host='0.0.0.0', port=5002, debug=True)
