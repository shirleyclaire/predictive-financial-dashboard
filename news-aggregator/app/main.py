from fastapi import FastAPI, HTTPException
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from .news_service import NewsService
from .models import SessionLocal, NewsArticle
from typing import List
from sqlalchemy.orm import Session
from fastapi import Depends

app = FastAPI()
news_service = NewsService()
scheduler = AsyncIOScheduler()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    scheduler.add_job(news_service.fetch_financial_news, 'interval', hours=1)
    scheduler.start()

@app.get("/news/", response_model=List[dict])
async def get_latest_news(db: Session = Depends(get_db)):
    articles = db.query(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(50).all()
    return articles

@app.get("/news/sentiment/{sentiment}")
async def get_news_by_sentiment(sentiment: str, db: Session = Depends(get_db)):
    articles = db.query(NewsArticle).filter(
        NewsArticle.sentiment_label == sentiment
    ).order_by(NewsArticle.published_at.desc()).all()
    return articles

@app.get("/news/analyze")
async def analyze_news():
    try:
        articles = await news_service.fetch_financial_news()
        return {"status": "success", "processed_articles": len(articles)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
