from newsapi import NewsApiClient
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime, timedelta
import os
from .models import NewsArticle, SessionLocal
from .rabbitmq_producer import RabbitMQProducer

class NewsService:
    def __init__(self):
        self.newsapi = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))
        self.tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        self.model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
        self.rabbitmq = RabbitMQProducer()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch_financial_news(self):
        try:
            news = self.newsapi.get_everything(
                q='finance OR stock market OR economy',
                language='en',
                sort_by='publishedAt',
                from_param=(datetime.now() - timedelta(hours=1)).isoformat()
            )
            
            processed_articles = []
            for article in news['articles']:
                sentiment = self._analyze_sentiment(article['title'] + " " + article.get('description', ''))
                
                news_article = NewsArticle(
                    title=article['title'],
                    content=article['description'],
                    source=article['source']['name'],
                    url=article['url'],
                    published_at=datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ'),
                    sentiment_score=sentiment['score'],
                    sentiment_label=sentiment['label']
                )
                processed_articles.append(news_article)
                
                # Notify other services if sentiment is significant
                if abs(sentiment['score']) > 0.7:
                    await self.rabbitmq.publish_news(news_article)
            
            # Store in database
            db = SessionLocal()
            try:
                db.add_all(processed_articles)
                db.commit()
            finally:
                db.close()
                
            return processed_articles
            
        except Exception as e:
            print(f"Error fetching news: {str(e)}")
            raise

    def _analyze_sentiment(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", max_length=512, truncation=True)
        outputs = self.model(**inputs)
        probabilities = torch.nn.functional.softmax(outputs.logits, dim=1)
        sentiment_score = float(probabilities[0][1] - probabilities[0][0])
        
        return {
            'score': sentiment_score,
            'label': 'positive' if sentiment_score > 0 else 'negative'
        }
