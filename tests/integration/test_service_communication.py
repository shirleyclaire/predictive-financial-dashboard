import pytest
import pika
import json
import asyncio
from datetime import datetime

@pytest.fixture
def rabbitmq_connection():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()
    yield channel
    connection.close()

@pytest.mark.asyncio
async def test_news_sentiment_propagation(rabbitmq_connection):
    # Publish test news sentiment
    test_sentiment = {
        'title': 'Test Economic News',
        'sentiment_score': 0.8,
        'url': 'http://test.com',
        'timestamp': datetime.now().isoformat()
    }
    
    rabbitmq_connection.basic_publish(
        exchange='financial_news',
        routing_key='news.sentiment',
        body=json.dumps(test_sentiment)
    )
    
    # Wait for processing
    await asyncio.sleep(2)
    
    # Verify prediction service received and processed sentiment
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/predictions/predict/test_user"
        )
        predictions = response.json()
        assert "sentiment_impact" in predictions
