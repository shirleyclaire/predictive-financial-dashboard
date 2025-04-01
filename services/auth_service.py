from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, constr
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from typing import Optional
from collections import defaultdict
from shared.config import get_settings

# Password and JWT configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
settings = get_settings()

# Update JWT configuration
JWT_SECRET = settings.JWT_SECRET
JWT_ALGORITHM = settings.JWT_ALGORITHM
JWT_EXPIRE_MINUTES = 30

# Rate limiting setup
RATE_LIMIT_DURATION = 60  # seconds
RATE_LIMIT_REQUESTS = 5   # requests per duration

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)

    def is_rate_limited(self, key: str) -> bool:
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=RATE_LIMIT_DURATION)
        
        # Clean old requests
        self.requests[key] = [req_time for req_time in self.requests[key] 
                            if req_time > cutoff]
        
        # Check limit
        if len(self.requests[key]) >= RATE_LIMIT_REQUESTS:
            return True
            
        self.requests[key].append(now)
        return False

rate_limiter = RateLimiter()

class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=8)
    full_name: str

class User(BaseModel):
    email: EmailStr
    hashed_password: str
    full_name: str
    disabled: bool = False

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    endpoint = request.url.path
    
    if rate_limiter.is_rate_limited(f"{client_ip}:{endpoint}"):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later."
        )
    
    response = await call_next(request)
    return response

app.middleware("http")(rate_limit_middleware)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=JWT_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

async def verify_token(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/register")
async def register_user(user: UserCreate):
    # In production, check if user exists in database
    hashed_password = get_password_hash(user.password)
    # Store user in database
    return {"message": "User created successfully"}

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # In production, validate against database
    if not form_data.username or not form_data.password:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    # Demo validation - replace with database check
    if form_data.username != "demo@example.com":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token({"sub": form_data.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRE_MINUTES * 60
    }
