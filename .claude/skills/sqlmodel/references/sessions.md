# Database Connection and Session Management

## Basic Engine Setup

```python
from sqlmodel import create_engine, SQLModel

# PostgreSQL connection
DATABASE_URL = "postgresql://user:password@localhost:5432/dbname"
engine = create_engine(DATABASE_URL, echo=True)  # echo=True for SQL logging

# Create all tables
SQLModel.metadata.create_all(engine)
```

## Environment-Based Configuration

```python
import os
from sqlmodel import create_engine

def get_database_url() -> str:
    """Get database URL from environment"""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/dbname"
    )

# Create engine
engine = create_engine(
    get_database_url(),
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"
)
```

## FastAPI Dependency Injection

```python
from sqlmodel import Session, create_engine
from typing import Generator
from fastapi import Depends

# Database URL
DATABASE_URL = "postgresql://user:password@localhost:5432/dbname"
engine = create_engine(DATABASE_URL)

def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency for database session"""
    with Session(engine) as session:
        yield session

# Usage in endpoint
from fastapi import FastAPI, Depends

app = FastAPI()

@app.get("/users/{user_id}")
def get_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    return user
```

## Session Configuration

```python
from sqlmodel import Session, create_engine

# Engine with custom settings
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Disable SQL logging
    pool_size=5,  # Connection pool size
    max_overflow=10,  # Maximum overflow connections
    pool_timeout=30,  # Timeout for getting connection from pool
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Verify connections before using
)

# Create session with custom settings
with Session(
    engine,
    expire_on_commit=False,  # Don't expire objects after commit
    autoflush=True,  # Auto flush before queries
    autocommit=False,  # Explicit commits
) as session:
    # Work with session
    pass
```

## Manual Transaction Control

```python
from sqlmodel import Session

def transfer_funds(from_user_id: int, to_user_id: int, amount: Decimal):
    with Session(engine) as session:
        try:
            # Disable autocommit
            from_user = session.get(User, from_user_id)
            to_user = session.get(User, to_user_id)

            from_user.balance -= amount
            to_user.balance += amount

            session.add(from_user)
            session.add(to_user)

            # Explicit commit
            session.commit()

            # Refresh to get updated values
            session.refresh(from_user)
            session.refresh(to_user)

        except Exception as e:
            # Automatic rollback on exception
            session.rollback()
            raise e
```

## Connection Pooling

```python
from sqlalchemy.pool import QueuePool, NullPool

# Default connection pool (QueuePool)
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,  # Connections to keep in pool
    max_overflow=20,  # Additional connections when pool is full
    pool_timeout=30,  # Seconds to wait for connection
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Disable connection pooling (for serverless)
engine_no_pool = create_engine(
    DATABASE_URL,
    poolclass=NullPool  # No connection pooling
)
```

## Multiple Database Engines

```python
# Primary database
primary_engine = create_engine("postgresql://localhost/primary")

# Read replica
replica_engine = create_engine("postgresql://localhost/replica")

# Usage
def get_primary_session():
    with Session(primary_engine) as session:
        yield session

def get_replica_session():
    with Session(replica_engine) as session:
        yield session

# In endpoints
@app.post("/users")
def create_user(user: UserCreate, session: Session = Depends(get_primary_session)):
    # Write to primary
    pass

@app.get("/users")
def list_users(session: Session = Depends(get_replica_session)):
    # Read from replica
    pass
```

## Async Sessions (SQLModel with asyncio)

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

# Async engine
async_engine = create_async_engine(
    "postgresql+asyncpg://user:password@localhost/dbname",
    echo=True,
    future=True
)

# Async session maker
async_session = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

# Usage in async endpoint
@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    from sqlalchemy import select
    statement = select(User).where(User.id == user_id)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    return user
```

## Session Scopes and Lifespan

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database lifecycle"""
    # Startup: create tables
    SQLModel.metadata.create_all(engine)
    yield
    # Shutdown: cleanup
    engine.dispose()

app = FastAPI(lifespan=lifespan)
```

## Best Practices

```python
# ✅ GOOD: Use context manager
def create_user(user_data: UserCreate):
    with Session(engine) as session:
        user = User(**user_data.dict())
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

# ❌ BAD: Don't forget to close
def create_user_bad(user_data: UserCreate):
    session = Session(engine)
    user = User(**user_data.dict())
    session.add(user)
    session.commit()
    # Session not closed!
    return user

# ✅ GOOD: Use dependency injection in FastAPI
@app.post("/users")
def create_user(
    user: UserCreate,
    session: Session = Depends(get_session)
):
    db_user = User(**user.dict())
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

# ❌ BAD: Creating session inside endpoint
@app.post("/users")
def create_user_bad(user: UserCreate):
    with Session(engine) as session:  # Creates new connection each time
        db_user = User(**user.dict())
        session.add(db_user)
        session.commit()
        return db_user
```

## Testing Configuration

```python
# Separate engine for testing
from sqlmodel import create_engine, SQLModel, Session

def get_test_engine():
    """Create in-memory SQLite engine for tests"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False
    )
    return engine

def get_test_session():
    """Get test session"""
    engine = get_test_engine()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

# Override dependency in tests
from fastapi.testclient import TestClient

def test_create_user():
    app.dependency_overrides[get_session] = get_test_session
    client = TestClient(app)
    response = client.post("/users", json={"username": "test"})
    assert response.status_code == 201
```
