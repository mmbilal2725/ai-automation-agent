# Advanced Features and Best Practices

## Transaction Management

### Manual Transactions

```python
from sqlmodel import Session
from sqlalchemy.exc import SQLAlchemyError

def transfer_balance(
    session: Session,
    from_user_id: int,
    to_user_id: int,
    amount: Decimal
):
    """Transfer balance between users with transaction"""
    try:
        # Begin transaction (implicit with Session)
        from_user = session.get(User, from_user_id)
        to_user = session.get(User, to_user_id)

        if not from_user or not to_user:
            raise ValueError("User not found")

        if from_user.balance < amount:
            raise ValueError("Insufficient balance")

        # Update balances
        from_user.balance -= amount
        to_user.balance += amount

        session.add(from_user)
        session.add(to_user)

        # Commit transaction
        session.commit()

        # Refresh to get updated values
        session.refresh(from_user)
        session.refresh(to_user)

        return {"success": True, "amount": amount}

    except SQLAlchemyError as e:
        # Automatic rollback on exception
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
```

### Nested Transactions (Savepoints)

```python
def complex_operation(session: Session):
    """Use savepoints for nested transactions"""
    # Main transaction
    user = User(username="testuser")
    session.add(user)

    # Create savepoint
    savepoint = session.begin_nested()

    try:
        # Risky operation
        post = Post(title="Test", user_id=user.id)
        session.add(post)
        session.flush()

        # If successful, commit savepoint
        savepoint.commit()

    except Exception as e:
        # Rollback to savepoint (main transaction continues)
        savepoint.rollback()
        print(f"Savepoint rolled back: {e}")

    # Commit main transaction
    session.commit()
```

### Transaction Isolation Levels

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Set isolation level on engine
engine = create_engine(
    DATABASE_URL,
    isolation_level="REPEATABLE READ"
)

# Or set per session
with Session(engine) as session:
    session.connection().execution_options(
        isolation_level="SERIALIZABLE"
    )
```

## Cascading Deletes

```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class Author(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    # CASCADE: Delete books when author is deleted
    books: List["Book"] = Relationship(
        back_populates="author",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class Book(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    author_id: int = Field(foreign_key="author.id")

    author: Author = Relationship(back_populates="books")

# Usage
with Session(engine) as session:
    author = session.get(Author, 1)
    session.delete(author)
    session.commit()
    # All books by this author are automatically deleted
```

### Cascade Options

```python
# Delete orphans when removed from parent
class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    members: List["Member"] = Relationship(
        back_populates="team",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan"
        }
    )

# Prevent deletion if children exist
class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    products: List["Product"] = Relationship(
        back_populates="category",
        sa_relationship_kwargs={
            "cascade": "save-update, merge"
        }
    )

# Set NULL on delete
from sqlalchemy import Column, Integer, ForeignKey

class Comment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    user_id: Optional[int] = Field(
        sa_column=Column(
            Integer,
            ForeignKey("user.id", ondelete="SET NULL")
        )
    )
```

## Soft Deletes

```python
from datetime import datetime
from typing import Optional

class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = None

class User(SQLModel, SoftDeleteMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str

# Soft delete function
def soft_delete(session: Session, model: SQLModel):
    """Soft delete a model instance"""
    model.is_deleted = True
    model.deleted_at = datetime.utcnow()
    session.add(model)
    session.commit()

# Query only non-deleted records
def get_active_users(session: Session):
    """Get only non-deleted users"""
    statement = select(User).where(User.is_deleted == False)
    return session.exec(statement).all()

# Restore soft-deleted record
def restore(session: Session, model: SQLModel):
    """Restore a soft-deleted record"""
    model.is_deleted = False
    model.deleted_at = None
    session.add(model)
    session.commit()
```

## Event Listeners

```python
from sqlalchemy import event
from datetime import datetime

class AuditMixin:
    """Mixin for audit fields"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class User(SQLModel, AuditMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str

# Auto-update timestamp on modification
@event.listens_for(User, 'before_update')
def receive_before_update(mapper, connection, target):
    """Update updated_at timestamp"""
    target.updated_at = datetime.utcnow()

# Validate before insert
@event.listens_for(User, 'before_insert')
def receive_before_insert(mapper, connection, target):
    """Validate user before insert"""
    if not target.username:
        raise ValueError("Username is required")
```

## Optimistic Locking

```python
class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str
    version: int = Field(default=1)

def update_with_optimistic_lock(
    session: Session,
    doc_id: int,
    new_content: str,
    expected_version: int
):
    """Update with optimistic locking"""
    statement = (
        update(Document)
        .where(
            Document.id == doc_id,
            Document.version == expected_version
        )
        .values(
            content=new_content,
            version=Document.version + 1
        )
    )

    result = session.execute(statement)
    session.commit()

    if result.rowcount == 0:
        raise HTTPException(
            status_code=409,
            detail="Document was modified by another user"
        )

    return session.get(Document, doc_id)
```

## Database-Level Constraints

```python
from sqlalchemy import CheckConstraint, UniqueConstraint, Index

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: Decimal
    stock: int
    category: str

    __table_args__ = (
        # Check constraint
        CheckConstraint('price > 0', name='check_positive_price'),
        CheckConstraint('stock >= 0', name='check_non_negative_stock'),

        # Unique constraint (composite)
        UniqueConstraint('name', 'category', name='uq_product_name_category'),

        # Index
        Index('ix_product_category_price', 'category', 'price'),

        # Partial index (PostgreSQL)
        Index(
            'ix_in_stock_products',
            'name',
            postgresql_where=text('stock > 0')
        ),
    )
```

## Custom Field Types

```python
from sqlalchemy import TypeDecorator, String
import json

class JSONEncodedDict(TypeDecorator):
    """Custom type for storing dict as JSON string"""
    impl = String

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

class Settings(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    preferences: dict = Field(sa_column=Column(JSONEncodedDict))
```

## Connection Pooling Advanced

```python
from sqlalchemy.pool import QueuePool, StaticPool, NullPool

# QueuePool (default) - Production
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True
)

# StaticPool - Single connection (testing)
engine = create_engine(
    "sqlite:///:memory:",
    poolclass=StaticPool,
    connect_args={"check_same_thread": False}
)

# NullPool - No pooling (serverless)
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool
)

# Custom pool events
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Set connection parameters"""
    dbapi_conn.execute("SET TIME ZONE 'UTC'")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Called when connection is retrieved from pool"""
    print("Connection checked out")

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """Called when connection is returned to pool"""
    print("Connection checked in")
```

## Security Best Practices

```python
# ✅ GOOD: Use parameterized queries (SQLModel does this automatically)
def get_user_by_email(session: Session, email: str):
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()

# ❌ BAD: Never use string formatting for queries
def get_user_bad(session: Session, email: str):
    query = f"SELECT * FROM user WHERE email = '{email}'"  # SQL injection!
    return session.execute(text(query))

# ✅ GOOD: Hash passwords
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# ✅ GOOD: Validate input
from pydantic import validator, EmailStr

class UserCreate(SQLModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)

    @validator('username')
    def username_alphanumeric(cls, v):
        assert v.isalnum(), 'must be alphanumeric'
        return v

# ✅ GOOD: Use environment variables for secrets
import os

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")

# ❌ BAD: Hardcode credentials
DATABASE_URL = "postgresql://admin:password123@localhost/db"  # Don't do this!
```

## Error Handling Best Practices

```python
from sqlalchemy.exc import (
    IntegrityError,
    DataError,
    OperationalError,
    DBAPIError
)
from fastapi import HTTPException

def create_user_safe(session: Session, user: UserCreate):
    """Create user with comprehensive error handling"""
    try:
        db_user = User(**user.dict())
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user

    except IntegrityError as e:
        session.rollback()
        if "unique constraint" in str(e).lower():
            raise HTTPException(
                status_code=409,
                detail="User with this email already exists"
            )
        raise HTTPException(status_code=409, detail="Database constraint violation")

    except DataError as e:
        session.rollback()
        raise HTTPException(status_code=400, detail="Invalid data format")

    except OperationalError as e:
        session.rollback()
        raise HTTPException(status_code=503, detail="Database unavailable")

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
```

## Monitoring and Logging

```python
import logging
from sqlalchemy import event
from time import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log slow queries
@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(
    conn, cursor, statement, parameters, context, executemany
):
    context._query_start_time = time()

@event.listens_for(engine, "after_cursor_execute")
def receive_after_cursor_execute(
    conn, cursor, statement, parameters, context, executemany
):
    total_time = time() - context._query_start_time

    if total_time > 1.0:  # Log queries slower than 1 second
        logger.warning(
            f"Slow query ({total_time:.2f}s): {statement[:100]}"
        )
```

## Testing Best Practices

```python
import pytest
from sqlmodel import create_engine, SQLModel, Session

@pytest.fixture(scope="function")
def test_engine():
    """Create test database for each test"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def test_session(test_engine):
    """Create test session"""
    with Session(test_engine) as session:
        yield session
        session.rollback()  # Rollback after each test

# Factory pattern for test data
def create_test_user(session: Session, **kwargs):
    """Factory for creating test users"""
    defaults = {
        "username": "testuser",
        "email": "test@example.com",
        "is_active": True
    }
    defaults.update(kwargs)

    user = User(**defaults)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# Usage in tests
def test_user_creation(test_session):
    user = create_test_user(test_session, username="john")
    assert user.username == "john"
```
