# FastAPI Integration Patterns

## Project Structure

```
app/
├── __init__.py
├── main.py              # FastAPI application
├── database.py          # Database configuration
├── models.py            # SQLModel models
├── schemas.py           # Pydantic schemas (if needed)
├── crud.py              # CRUD operations
├── dependencies.py      # FastAPI dependencies
├── routers/
│   ├── __init__.py
│   ├── users.py         # User routes
│   └── posts.py         # Post routes
└── config.py            # Configuration
```

## Database Configuration

```python
# app/database.py
from sqlmodel import create_engine, Session, SQLModel
from typing import Generator
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/dbname"
)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

def create_db_and_tables():
    """Create database tables"""
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """Dependency for database session"""
    with Session(engine) as session:
        yield session
```

## Application Lifespan

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import create_db_and_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    print("Creating database tables...")
    create_db_and_tables()
    print("Application started")

    yield

    # Shutdown
    print("Application shutting down...")

app = FastAPI(lifespan=lifespan)
```

## Models and Schemas

```python
# app/models.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

# Table models
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=50)
    email: str = Field(unique=True, index=True, max_length=100)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Request/Response models
class UserCreate(SQLModel):
    username: str = Field(max_length=50)
    email: str = Field(max_length=100)
    password: str = Field(min_length=8)

class UserUpdate(SQLModel):
    username: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=100)
    password: Optional[str] = Field(default=None, min_length=8)

class UserRead(SQLModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
```

## CRUD Layer

```python
# app/crud.py
from sqlmodel import Session, select
from app.models import User, UserCreate, UserUpdate
from typing import Optional, List
from fastapi import HTTPException

def create_user(session: Session, user: UserCreate) -> User:
    """Create new user"""
    # Hash password (use proper hashing in production)
    hashed_password = hash_password(user.password)

    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

def get_user(session: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return session.get(User, user_id)

def get_user_by_email(session: Session, email: str) -> Optional[User]:
    """Get user by email"""
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()

def get_users(
    session: Session,
    skip: int = 0,
    limit: int = 100
) -> List[User]:
    """Get all users with pagination"""
    statement = select(User).offset(skip).limit(limit)
    return session.exec(statement).all()

def update_user(
    session: Session,
    user_id: int,
    user_update: UserUpdate
) -> User:
    """Update user"""
    db_user = get_user(session, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_update.dict(exclude_unset=True)

    if "password" in update_data:
        update_data["hashed_password"] = hash_password(update_data.pop("password"))

    for key, value in update_data.items():
        setattr(db_user, key, value)

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

def delete_user(session: Session, user_id: int) -> None:
    """Delete user"""
    db_user = get_user(session, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    session.delete(db_user)
    session.commit()
```

## Router Implementation

```python
# app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List
from app.database import get_session
from app.models import UserCreate, UserUpdate, UserRead
from app import crud

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    session: Session = Depends(get_session)
):
    """Create a new user"""
    # Check if user exists
    if crud.get_user_by_email(session, user.email):
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    return crud.create_user(session, user)

@router.get("/{user_id}", response_model=UserRead)
def read_user(
    user_id: int,
    session: Session = Depends(get_session)
):
    """Get user by ID"""
    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("", response_model=List[UserRead])
def read_users(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """Get all users"""
    return crud.get_users(session, skip=skip, limit=limit)

@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user: UserUpdate,
    session: Session = Depends(get_session)
):
    """Update user"""
    return crud.update_user(session, user_id, user)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    session: Session = Depends(get_session)
):
    """Delete user"""
    crud.delete_user(session, user_id)
```

## Main Application

```python
# app/main.py
from fastapi import FastAPI
from app.routers import users, posts

app = FastAPI(
    title="My API",
    description="API built with FastAPI and SQLModel",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(users.router)
app.include_router(posts.router)

@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "Welcome to the API"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
```

## Custom Dependencies

```python
# app/dependencies.py
from fastapi import Depends, HTTPException, status
from sqlmodel import Session
from app.database import get_session
from app.models import User
from app.crud import get_user

def get_current_user(
    user_id: int,
    session: Session = Depends(get_session)
) -> User:
    """Get current authenticated user"""
    user = get_user(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verify user is active"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Usage in endpoint
@router.get("/me", response_model=UserRead)
def read_current_user(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user info"""
    return current_user
```

## Response Models with Relationships

```python
from typing import List

# Model with relationships
class UserWithPosts(UserRead):
    posts: List["PostRead"] = []

# Endpoint returning relationships
@router.get("/{user_id}/with-posts", response_model=UserWithPosts)
def read_user_with_posts(
    user_id: int,
    session: Session = Depends(get_session)
):
    """Get user with all posts"""
    from sqlalchemy.orm import selectinload

    statement = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.posts))
    )
    user = session.exec(statement).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
```

## Configuration Management

```python
# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "My API"
    database_url: str = "postgresql://localhost/dbname"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

# Usage
from app.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url)
```

## Error Handling

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors"""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Database constraint violation"}
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle value errors"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )
```

## Middleware Integration

```python
from fastapi import Request
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    """Ensure database session is always closed"""
    try:
        response = await call_next(request)
        return response
    finally:
        # Cleanup if needed
        pass
```

## Background Tasks

```python
from fastapi import BackgroundTasks

def send_email_notification(email: str, message: str):
    """Send email in background"""
    # Email sending logic
    print(f"Sending email to {email}: {message}")

@router.post("/{user_id}/notify")
def notify_user(
    user_id: int,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    """Send notification to user"""
    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    background_tasks.add_task(
        send_email_notification,
        user.email,
        "Welcome to our platform!"
    )

    return {"message": "Notification will be sent"}
```

## WebSocket Integration

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    session: Session = Depends(get_session)
):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Message: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```
