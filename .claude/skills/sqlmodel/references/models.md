# SQLModel Basics - Models and Fields

## Basic Model Definition

```python
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, max_length=50)
    email: str = Field(unique=True, max_length=100)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

## Field Types and Constraints

```python
from decimal import Decimal
from enum import Enum

class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # String fields
    name: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)

    # Numeric fields
    price: Decimal = Field(max_digits=10, decimal_places=2)
    stock: int = Field(ge=0)  # Greater than or equal to 0

    # Enum fields
    status: Status = Field(default=Status.PENDING)

    # Indexes
    sku: str = Field(unique=True, index=True, max_length=50)
    category: str = Field(index=True, max_length=100)
```

## Optional vs Required Fields

```python
class Task(SQLModel, table=True):
    # Required field (no Optional, no default)
    title: str

    # Optional field with None default
    description: Optional[str] = None

    # Optional field with explicit default
    priority: int = Field(default=1, ge=1, le=5)

    # Auto-generated fields
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

## Table Configuration

```python
class Article(SQLModel, table=True):
    __tablename__ = "articles"  # Custom table name
    __table_args__ = (
        {"comment": "Blog articles table"},  # Table comment
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200)
    slug: str = Field(unique=True, max_length=200)
    content: str
```

## Request/Response Models

```python
# Base model with shared fields
class UserBase(SQLModel):
    username: str = Field(max_length=50)
    email: str = Field(max_length=100)

# Table model
class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Request model (no password hash, no timestamps)
class UserCreate(UserBase):
    password: str = Field(min_length=8)

# Update model (all fields optional)
class UserUpdate(SQLModel):
    username: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=100)

# Response model (no password, includes timestamps)
class UserRead(UserBase):
    id: int
    created_at: datetime
```

## Computed Fields

```python
from sqlmodel import Field, Column
from sqlalchemy import String, computed

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    quantity: int
    unit_price: Decimal

    # Computed column (database-level)
    full_name: str = Field(
        sa_column=Column(
            String,
            computed("first_name || ' ' || last_name")
        )
    )
    total_price: Decimal = Field(
        sa_column=Column(
            computed("quantity * unit_price")
        )
    )
```

## JSON Fields

```python
from typing import Dict, Any
from sqlmodel import Column
from sqlalchemy.dialects.postgresql import JSON, JSONB

class Settings(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # JSON field (standard JSON)
    config: Dict[str, Any] = Field(sa_column=Column(JSON))

    # JSONB field (binary JSON, better performance in PostgreSQL)
    metadata: Dict[str, Any] = Field(sa_column=Column(JSONB))
```

## UUID Primary Keys

```python
from uuid import UUID, uuid4

class Session(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: int
    token: str
    expires_at: datetime
```

## Composite Primary Keys

```python
class Enrollment(SQLModel, table=True):
    student_id: int = Field(foreign_key="student.id", primary_key=True)
    course_id: int = Field(foreign_key="course.id", primary_key=True)
    enrolled_at: datetime = Field(default_factory=datetime.utcnow)
    grade: Optional[float] = None
```
