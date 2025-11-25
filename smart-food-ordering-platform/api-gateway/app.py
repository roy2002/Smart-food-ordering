"""
API Gateway Service
Central entry point for all microservices - implements API Gateway pattern
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import grpc
import os
import jwt
from functools import wraps
import sys
sys.path.append('./proto')

# Import gRPC generated files (will be generated later)
try:
    import order_pb2
    import order_pb2_grpc
except ImportError:
    print("Warning: gRPC files not generated yet. Run: python -m grpc_tools.protoc")

app = Flask(__name__)
CORS(app)

# Service URLs from environment variables
USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://localhost:5001')
RESTAURANT_SERVICE_URL = os.getenv('RESTAURANT_SERVICE_URL', 'http://localhost:5002')
ORDER_SERVICE_URL = os.getenv('ORDER_SERVICE_URL', 'localhost:50051')
RECOMMENDATION_SERVICE_URL = os.getenv('RECOMMENDATION_SERVICE_URL', 'http://localhost:5004')

JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')

# Circuit Breaker Configuration
CIRCUIT_BREAKER_THRESHOLD = 5
CIRCUIT_BREAKER_TIMEOUT = 60

class CircuitBreaker:
    """Simple Circuit Breaker implementation"""
    def __init__(self, threshold=5, timeout=60):
        self.threshold = threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if (time.time() - self.last_failure_time) > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.threshold:
                self.state = 'OPEN'
            raise e

# Circuit breakers for each service
circuit_breakers = {
    'user': CircuitBreaker(),
    'restaurant': CircuitBreaker(),
    'order': CircuitBreaker(),
    'recommendation': CircuitBreaker()
}

# Authentication decorator
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'No authorization token provided'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            request.user_id = payload.get('user_id')
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

# Health Check
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'api-gateway'}), 200

# ============= USER SERVICE ROUTES (REST) =============
@app.route('/api/users/register', methods=['POST'])
def register_user():
    try:
        response = circuit_breakers['user'].call(
            requests.post,
            f'{USER_SERVICE_URL}/api/users/register',
            json=request.json,
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': f'User service unavailable: {str(e)}'}), 503

@app.route('/api/users/login', methods=['POST'])
def login_user():
    try:
        response = circuit_breakers['user'].call(
            requests.post,
            f'{USER_SERVICE_URL}/api/users/login',
            json=request.json,
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': f'User service unavailable: {str(e)}'}), 503

@app.route('/api/users/<user_id>', methods=['GET'])
@require_auth
def get_user(user_id):
    try:
        response = circuit_breakers['user'].call(
            requests.get,
            f'{USER_SERVICE_URL}/api/users/{user_id}',
            headers={'Authorization': request.headers.get('Authorization')},
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': f'User service unavailable: {str(e)}'}), 503

# ============= RESTAURANT SERVICE ROUTES (REST) =============
@app.route('/api/restaurants', methods=['GET'])
def get_restaurants():
    try:
        params = request.args.to_dict()
        response = circuit_breakers['restaurant'].call(
            requests.get,
            f'{RESTAURANT_SERVICE_URL}/api/restaurants',
            params=params,
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': f'Restaurant service unavailable: {str(e)}'}), 503

@app.route('/api/restaurants/<restaurant_id>', methods=['GET'])
def get_restaurant(restaurant_id):
    try:
        response = circuit_breakers['restaurant'].call(
            requests.get,
            f'{RESTAURANT_SERVICE_URL}/api/restaurants/{restaurant_id}',
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': f'Restaurant service unavailable: {str(e)}'}), 503

@app.route('/api/restaurants/<restaurant_id>/menu', methods=['GET'])
def get_restaurant_menu(restaurant_id):
    try:
        response = circuit_breakers['restaurant'].call(
            requests.get,
            f'{RESTAURANT_SERVICE_URL}/api/restaurants/{restaurant_id}/menu',
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': f'Restaurant service unavailable: {str(e)}'}), 503

# ============= ORDER SERVICE ROUTES (gRPC) =============
@app.route('/api/orders', methods=['POST'])
@require_auth
def create_order():
    try:
        # Connect to gRPC service
        channel = grpc.insecure_channel(ORDER_SERVICE_URL)
        stub = order_pb2_grpc.OrderServiceStub(channel)
        
        data = request.json
        order_request = order_pb2.CreateOrderRequest(
            user_id=str(request.user_id),
            restaurant_id=data.get('restaurant_id'),
            items=str(data.get('items')),
            total_amount=float(data.get('total_amount', 0))
        )
        
        response = circuit_breakers['order'].call(
            stub.CreateOrder,
            order_request,
            timeout=5
        )
        
        return jsonify({
            'order_id': response.order_id,
            'status': response.status,
            'message': response.message
        }), 201
    except Exception as e:
        return jsonify({'error': f'Order service unavailable: {str(e)}'}), 503

@app.route('/api/orders/<order_id>', methods=['GET'])
@require_auth
def get_order(order_id):
    try:
        channel = grpc.insecure_channel(ORDER_SERVICE_URL)
        stub = order_pb2_grpc.OrderServiceStub(channel)
        
        order_request = order_pb2.GetOrderRequest(order_id=order_id)
        response = circuit_breakers['order'].call(
            stub.GetOrder,
            order_request,
            timeout=5
        )
        
        return jsonify({
            'order_id': response.order_id,
            'user_id': response.user_id,
            'restaurant_id': response.restaurant_id,
            'status': response.status,
            'total_amount': response.total_amount
        }), 200
    except Exception as e:
        return jsonify({'error': f'Order service unavailable: {str(e)}'}), 503

# ============= RECOMMENDATION SERVICE ROUTES (GraphQL) =============
@app.route('/api/recommendations', methods=['POST'])
@require_auth
def get_recommendations():
    """Forward GraphQL query to recommendation service"""
    try:
        response = circuit_breakers['recommendation'].call(
            requests.post,
            f'{RECOMMENDATION_SERVICE_URL}/graphql',
            json=request.json,
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': f'Recommendation service unavailable: {str(e)}'}), 503

# ============= RATE LIMITING (Simple Implementation) =============
from collections import defaultdict
import time

request_counts = defaultdict(list)
RATE_LIMIT = 100  # requests per minute
RATE_WINDOW = 60  # seconds

@app.before_request
def rate_limit():
    client_ip = request.remote_addr
    current_time = time.time()
    
    # Clean old requests
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip]
        if current_time - req_time < RATE_WINDOW
    ]
    
    # Check rate limit
    if len(request_counts[client_ip]) >= RATE_LIMIT:
        return jsonify({'error': 'Rate limit exceeded'}), 429
    
    # Add current request
    request_counts[client_ip].append(current_time)

if __name__ == '__main__':
    print("Starting API Gateway on port 8000...")
    print(f"User Service: {USER_SERVICE_URL}")
    print(f"Restaurant Service: {RESTAURANT_SERVICE_URL}")
    print(f"Order Service: {ORDER_SERVICE_URL}")
    print(f"Recommendation Service: {RECOMMENDATION_SERVICE_URL}")
    app.run(host='0.0.0.0', port=8000, debug=True)
