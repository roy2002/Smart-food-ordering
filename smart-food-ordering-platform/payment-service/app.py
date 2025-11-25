"""
Payment Service - Message Broker (Event-Driven)
Listens to order events and processes payments
Implements Saga Pattern - responds with payment status
"""

import pika
import json
import os
import time
import random
from datetime import datetime

# RabbitMQ configuration
RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://admin:password@localhost:5672/')

class PaymentService:
    
    def __init__(self, rabbitmq_url):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None
        self.connect()
    
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
                
                # Declare queues
                self.channel.queue_declare(queue='payment_queue', durable=True)
                
                # Bind queue to exchange
                self.channel.queue_bind(
                    exchange='order_events',
                    queue='payment_queue',
                    routing_key='order.created'
                )
                
                print("Connected to RabbitMQ successfully!")
                return
                
            except Exception as e:
                retry_count += 1
                print(f"Failed to connect to RabbitMQ (attempt {retry_count}/{max_retries}): {str(e)}")
                if retry_count < max_retries:
                    time.sleep(5)
                else:
                    raise Exception("Could not connect to RabbitMQ after multiple attempts")
    
    def process_payment(self, order_data):
        """
        Process payment for an order
        Simulates payment processing with random success/failure
        In production, this would integrate with payment gateways like Stripe, PayPal, etc.
        """
        order_id = order_data.get('order_id')
        total_amount = order_data.get('total_amount')
        payment_method = order_data.get('payment_method', 'CARD')
        
        print(f"\n{'='*50}")
        print(f"Processing payment for Order #{order_id}")
        print(f"Amount: ${total_amount}")
        print(f"Payment Method: {payment_method}")
        print(f"{'='*50}")
        
        # Simulate payment processing delay
        time.sleep(2)
        
        # Simulate 90% success rate
        success = random.random() < 0.9
        
        if success:
            print(f"✓ Payment successful for Order #{order_id}")
            
            # Publish payment.completed event (Saga Pattern - Step 2)
            payment_event = {
                'order_id': order_id,
                'payment_id': f"PAY_{order_id}_{int(time.time())}",
                'status': 'COMPLETED',
                'amount': total_amount,
                'payment_method': payment_method,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.publish_event('payment.completed', payment_event)
            
            # Also update order status
            self.publish_event('order.status_updated', {
                'order_id': order_id,
                'new_status': 'CONFIRMED',
                'timestamp': datetime.utcnow().isoformat()
            })
            
        else:
            print(f"✗ Payment failed for Order #{order_id}")
            
            # Publish payment.failed event (Saga Pattern - Compensation)
            payment_event = {
                'order_id': order_id,
                'status': 'FAILED',
                'reason': 'Insufficient funds or payment gateway error',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.publish_event('payment.failed', payment_event)
            
            # Trigger order cancellation (compensation transaction)
            self.publish_event('order.status_updated', {
                'order_id': order_id,
                'new_status': 'CANCELLED',
                'reason': 'Payment failed',
                'timestamp': datetime.utcnow().isoformat()
            })
    
    def publish_event(self, routing_key, message):
        """Publish event to RabbitMQ"""
        try:
            self.channel.basic_publish(
                exchange='order_events',
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            print(f"→ Published event: {routing_key}")
        except Exception as e:
            print(f"Failed to publish event: {str(e)}")
    
    def on_order_created(self, ch, method, properties, body):
        """
        Callback when order.created event is received
        Part of Saga Pattern orchestration
        """
        try:
            order_data = json.loads(body)
            print(f"\n← Received order.created event")
            
            # Process the payment
            self.process_payment(order_data)
            
            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            print(f"Error processing order: {str(e)}")
            # Negative acknowledgment - message will be requeued
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start_consuming(self):
        """Start listening for order events"""
        print("\n" + "="*50)
        print("Payment Service Started")
        print("="*50)
        print("Waiting for order events...")
        print("Press CTRL+C to exit\n")
        
        # Set QoS - process one message at a time
        self.channel.basic_qos(prefetch_count=1)
        
        # Start consuming
        self.channel.basic_consume(
            queue='payment_queue',
            on_message_callback=self.on_order_created
        )
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print("\nShutting down Payment Service...")
            self.channel.stop_consuming()
        finally:
            if self.connection:
                self.connection.close()

def main():
    """Main entry point"""
    print("Initializing Payment Service...")
    print(f"RabbitMQ URL: {RABBITMQ_URL}")
    
    payment_service = PaymentService(RABBITMQ_URL)
    payment_service.start_consuming()

if __name__ == '__main__':
    main()
