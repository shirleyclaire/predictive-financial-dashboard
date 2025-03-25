import pika
import json
from tenacity import retry, stop_after_attempt, wait_exponential
import os
from .prediction_service import PredictionService

class RabbitMQConsumer:
    def __init__(self, prediction_service: PredictionService):
        self.prediction_service = prediction_service
        self.connection = None
        self.channel = None
        self.connect()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def connect(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=os.getenv('RABBITMQ_HOST', 'rabbitmq'))
        )
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='financial_news', exchange_type='topic')
        
        result = self.channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        self.channel.queue_bind(
            exchange='financial_news',
            queue=queue_name,
            routing_key='news.sentiment'
        )
        
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=self.process_message,
            auto_ack=True
        )

    def process_message(self, ch, method, properties, body):
        try:
            message = json.loads(body)
            self.prediction_service.update_sentiment_impact(message['sentiment_score'])
        except Exception as e:
            print(f"Error processing message: {str(e)}")

    def start_consuming(self):
        self.channel.start_consuming()
