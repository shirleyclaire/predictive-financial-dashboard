import pika
import json
from tenacity import retry, stop_after_attempt, wait_exponential
import os

class RabbitMQProducer:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.connect()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def connect(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=os.getenv('RABBITMQ_HOST', 'rabbitmq'))
        )
        self.channel = self.connection.channel()
        self.channel.exchange_declare(
            exchange='financial_news',
            exchange_type='topic'
        )

    async def publish_news(self, news_article):
        try:
            message = {
                'title': news_article.title,
                'sentiment_score': news_article.sentiment_score,
                'url': news_article.url,
                'timestamp': news_article.published_at.isoformat()
            }
            
            self.channel.basic_publish(
                exchange='financial_news',
                routing_key='news.sentiment',
                body=json.dumps(message)
            )
        except (pika.exceptions.AMQPError, ConnectionError):
            self.connect()
            await self.publish_news(news_article)
