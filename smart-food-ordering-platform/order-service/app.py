"""
Order Service - gRPC API
Manages order creation, tracking, and status updates
Implements Saga Pattern for distributed transactions
"""

import grpc
from concurrent import futures
import time
import os
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pika
import sys
import threading

# Add proto directory to path
sys.path.append('./proto')

# Import generated gRPC code
import order_pb2
import order_pb2_grpc

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5434/orderdb')
RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://admin:password@localhost:5672/')

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Order Model
class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    restaurant_id = Column(Integer, nullable=False)
    items = Column(Text, nullable=False)  # JSON string
    status = Column(String, default='PENDING')  # PENDING, CONFIRMED, PREPARING, READY, DELIVERED, CANCELLED
    total_amount = Column(Float, nullable=False)
    delivery_address = Column(Text)
    payment_method = Column(String, default='CARD')
    payment_status = Column(String, default='PENDING')  # PENDING, COMPLETED, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# RabbitMQ Publisher for Saga Pattern
class MessagePublisher:
    def __init__(self, rabbitmq_url):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None
    
    def connect(self):
        """Connect to RabbitMQ"""
        try:
            self.connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
            self.channel = self.connection.channel()
            
            # Declare exchanges
            self.channel.exchange_declare(exchange='order_events', exchange_type='topic', durable=True)
            print("Connected to RabbitMQ")
        except Exception as e:
            print(f"Failed to connect to RabbitMQ: {str(e)}")
    
    def publish_event(self, routing_key, message):
        """Publish event to RabbitMQ with auto-reconnect"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Check if channel is open, reconnect if needed
                if not self.channel or self.channel.is_closed:
                    print(f"Reconnecting to RabbitMQ (attempt {attempt + 1}/{max_retries})...")
                    self.connect()
                
                self.channel.basic_publish(
                    exchange='order_events',
                    routing_key=routing_key,
                    body=json.dumps(message),
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # Make message persistent
                    )
                )
                print(f"Published event: {routing_key}")
                return  # Success, exit the function
                
            except Exception as e:
                print(f"Failed to publish event (attempt {attempt + 1}/{max_retries}): {str(e)}")
                # Close and clear connection for retry
                try:
                    if self.connection and self.connection.is_open:
                        self.connection.close()
                except:
                    pass
                self.connection = None
                self.channel = None
                
                if attempt < max_retries - 1:
                    time.sleep(1)  # Wait before retry
                else:
                    print(f"ERROR: Failed to publish event after {max_retries} attempts")
    
    def close(self):
        """Close connection"""
        if self.connection:
            self.connection.close()

# Initialize message publisher
message_publisher = MessagePublisher(RABBITMQ_URL)
message_publisher.connect()

# RabbitMQ Consumer for Saga Pattern - listens for payment events
class MessageConsumer:
    def __init__(self, rabbitmq_url):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None
    
    def connect(self):
        """Connect to RabbitMQ"""
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                self.connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
                self.channel = self.connection.channel()
                
                # Declare exchange
                self.channel.exchange_declare(exchange='order_events', exchange_type='topic', durable=True)
                
                # Declare queue for order status updates
                self.channel.queue_declare(queue='order_status_queue', durable=True)
                
                # Bind queue to exchange for status updates
                self.channel.queue_bind(
                    exchange='order_events',
                    queue='order_status_queue',
                    routing_key='order.status_updated'
                )
                
                print("Consumer connected to RabbitMQ")
                return
                
            except Exception as e:
                retry_count += 1
                print(f"Failed to connect consumer to RabbitMQ (attempt {retry_count}/{max_retries}): {str(e)}")
                if retry_count < max_retries:
                    time.sleep(5)
                else:
                    raise Exception("Could not connect consumer to RabbitMQ after multiple attempts")
    
    def on_status_update(self, ch, method, properties, body):
        """Handle order status update events from payment service"""
        try:
            update_data = json.loads(body)
            order_id = update_data.get('order_id')
            new_status = update_data.get('new_status')
            
            print(f"\n← Received order.status_updated event for Order #{order_id}: {new_status}")
            
            # Update order in database
            db = SessionLocal()
            try:
                order = db.query(Order).filter(Order.id == int(order_id)).first()
                if order:
                    order.status = new_status
                    order.updated_at = datetime.utcnow()
                    
                    # If payment was successful, update payment status
                    if new_status == 'CONFIRMED':
                        order.payment_status = 'COMPLETED'
                    elif new_status == 'CANCELLED':
                        order.payment_status = 'FAILED'
                    
                    db.commit()
                    print(f"✓ Updated Order #{order_id} status to {new_status}")
                else:
                    print(f"✗ Order #{order_id} not found")
            finally:
                db.close()
            
            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            print(f"Error processing status update: {str(e)}")
            # Negative acknowledgment - message will be requeued
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start_consuming(self):
        """Start listening for order status update events"""
        print("\nOrder Status Update Consumer Started")
        print("Waiting for status update events...")
        
        # Set QoS - process one message at a time
        self.channel.basic_qos(prefetch_count=1)
        
        # Start consuming
        self.channel.basic_consume(
            queue='order_status_queue',
            on_message_callback=self.on_status_update
        )
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print("\nShutting down Order Status Consumer...")
            self.channel.stop_consuming()
        finally:
            if self.connection:
                self.connection.close()

# Initialize message consumer
message_consumer = MessageConsumer(RABBITMQ_URL)

# gRPC Service Implementation
class OrderServiceServicer(order_pb2_grpc.OrderServiceServicer):
    
    def CreateOrder(self, request, context):
        """Create a new order - implements Saga Pattern"""
        db = SessionLocal()
        try:
            # Create order
            new_order = Order(
                user_id=int(request.user_id),
                restaurant_id=int(request.restaurant_id),
                items=request.items,
                total_amount=request.total_amount,
                delivery_address=request.delivery_address,
                payment_method=request.payment_method,
                status='PENDING'
            )
            
            db.add(new_order)
            db.commit()
            db.refresh(new_order)
            
            # Publish order.created event (Saga Pattern - Step 1)
            message_publisher.publish_event(
                'order.created',
                {
                    'order_id': new_order.id,
                    'user_id': new_order.user_id,
                    'restaurant_id': new_order.restaurant_id,
                    'total_amount': new_order.total_amount,
                    'payment_method': new_order.payment_method,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            return order_pb2.CreateOrderResponse(
                order_id=str(new_order.id),
                status='PENDING',
                message='Order created successfully. Awaiting payment confirmation.'
            )
            
        except Exception as e:
            db.rollback()
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f'Failed to create order: {str(e)}')
            return order_pb2.CreateOrderResponse(
                order_id='',
                status='FAILED',
                message=f'Order creation failed: {str(e)}'
            )
        finally:
            db.close()
    
    def GetOrder(self, request, context):
        """Get order details"""
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.id == int(request.order_id)).first()
            
            if not order:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details('Order not found')
                return order_pb2.GetOrderResponse()
            
            return order_pb2.GetOrderResponse(
                order_id=str(order.id),
                user_id=str(order.user_id),
                restaurant_id=str(order.restaurant_id),
                items=order.items,
                status=order.status,
                total_amount=order.total_amount,
                delivery_address=order.delivery_address or '',
                created_at=order.created_at.isoformat() if order.created_at else ''
            )
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f'Failed to fetch order: {str(e)}')
            return order_pb2.GetOrderResponse()
        finally:
            db.close()
    
    def UpdateOrderStatus(self, request, context):
        """Update order status - part of Saga Pattern"""
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.id == int(request.order_id)).first()
            
            if not order:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details('Order not found')
                return order_pb2.UpdateOrderStatusResponse(
                    order_id='',
                    status='',
                    message='Order not found'
                )
            
            old_status = order.status
            order.status = request.status
            order.updated_at = datetime.utcnow()
            
            db.commit()
            
            # Publish status update event
            message_publisher.publish_event(
                'order.status_updated',
                {
                    'order_id': order.id,
                    'old_status': old_status,
                    'new_status': order.status,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            return order_pb2.UpdateOrderStatusResponse(
                order_id=str(order.id),
                status=order.status,
                message=f'Order status updated to {order.status}'
            )
            
        except Exception as e:
            db.rollback()
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f'Failed to update order status: {str(e)}')
            return order_pb2.UpdateOrderStatusResponse(
                order_id='',
                status='',
                message=f'Update failed: {str(e)}'
            )
        finally:
            db.close()
    
    def ListUserOrders(self, request, context):
        """List all orders for a user"""
        db = SessionLocal()
        try:
            query = db.query(Order).filter(Order.user_id == int(request.user_id))
            
            # Pagination
            limit = request.limit if request.limit > 0 else 10
            offset = request.offset if request.offset >= 0 else 0
            
            total = query.count()
            orders = query.order_by(Order.created_at.desc()).limit(limit).offset(offset).all()
            
            order_responses = []
            for order in orders:
                order_responses.append(
                    order_pb2.GetOrderResponse(
                        order_id=str(order.id),
                        user_id=str(order.user_id),
                        restaurant_id=str(order.restaurant_id),
                        items=order.items,
                        status=order.status,
                        total_amount=order.total_amount,
                        delivery_address=order.delivery_address or '',
                        created_at=order.created_at.isoformat() if order.created_at else ''
                    )
                )
            
            return order_pb2.ListUserOrdersResponse(
                orders=order_responses,
                total=total
            )
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f'Failed to list orders: {str(e)}')
            return order_pb2.ListUserOrdersResponse(orders=[], total=0)
        finally:
            db.close()

def serve():
    """Start gRPC server and RabbitMQ consumer"""
    # Start RabbitMQ consumer in a separate thread
    def run_consumer():
        try:
            message_consumer.connect()
            message_consumer.start_consuming()
        except Exception as e:
            print(f"Consumer thread error: {str(e)}")
    
    consumer_thread = threading.Thread(target=run_consumer, daemon=True)
    consumer_thread.start()
    print("Order Status Consumer thread started")
    
    # Start gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    order_pb2_grpc.add_OrderServiceServicer_to_server(OrderServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Order Service (gRPC) started on port 50051...")
    print(f"Database: {DATABASE_URL}")
    print(f"RabbitMQ: {RABBITMQ_URL}")
    
    try:
        while True:
            time.sleep(86400)  # Keep server running
    except KeyboardInterrupt:
        server.stop(0)
        message_publisher.close()

if __name__ == '__main__':
    serve()
