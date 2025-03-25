from fastapi import FastAPI, HTTPException
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
from datetime import datetime
from typing import List, Dict
from .prediction_service import PredictionService
from .rabbitmq_consumer import RabbitMQConsumer
import threading

app = FastAPI()
prediction_service = PredictionService()
scheduler = AsyncIOScheduler()
rabbitmq_consumer = RabbitMQConsumer(prediction_service)

@app.on_event("startup")
async def startup_event():
    # Start RabbitMQ consumer in a separate thread
    consumer_thread = threading.Thread(target=rabbitmq_consumer.start_consuming)
    consumer_thread.daemon = True
    consumer_thread.start()
    
    # Schedule weekly model retraining
    scheduler.add_job(prediction_service.train_model, 'interval', weeks=1)
    scheduler.start()

@app.post("/train")
async def train_model(transactions: List[Dict]):
    await prediction_service.train_model(transactions)
    return {"status": "success", "message": "Model trained successfully"}

@app.get("/predict/{user_id}")
async def get_prediction(user_id: str, days: int = 30):
    if days not in [30, 60, 90]:
        raise HTTPException(status_code=400, detail="Days must be 30, 60, or 90")
    
    try:
        predictions = await prediction_service.predict(days, user_id)
        plot = prediction_service.generate_plot(predictions)
        return {
            "predictions": predictions,
            "plot": plot
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
