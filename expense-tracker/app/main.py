from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from . import models, schemas, crud
from .database import engine, get_db
from .redis_cache import RedisCache
import json

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
redis_cache = RedisCache()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db=db, user=user)

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return crud.authenticate_user(db, form_data.username, form_data.password)

@app.post("/transactions/", response_model=schemas.Transaction)
async def create_transaction(
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(crud.get_current_user)
):
    redis_cache.invalidate_user_cache(current_user.id)
    return crud.create_transaction(db=db, transaction=transaction, user_id=current_user.id)

@app.get("/transactions/summary/monthly")
async def get_monthly_summary(
    current_user: models.User = Depends(crud.get_current_user),
    db: Session = Depends(get_db)
):
    cache_key = f"monthly_summary:{current_user.id}"
    cached_data = redis_cache.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    
    summary = crud.get_monthly_summary(db, current_user.id)
    redis_cache.set(cache_key, json.dumps(summary), 3600)  # Cache for 1 hour
    return summary
