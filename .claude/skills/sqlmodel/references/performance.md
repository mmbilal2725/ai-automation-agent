# Performance Optimization

## Connection Pooling

```python
from sqlmodel import create_engine
from sqlalchemy.pool import QueuePool

# Optimized connection pool
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,  # Number of connections to keep
    max_overflow=40,  # Additional connections when pool is full
    pool_timeout=30,  # Wait time for connection (seconds)
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Test connection before using
    echo_pool=False,  # Log pool checkouts/checkins
)
```

## Query Optimization

### N+1 Query Problem

```python
# ❌ BAD: N+1 queries
def get_users_with_posts_bad(session: Session):
    users = session.exec(select(User)).all()
    for user in users:
        # Each access triggers a new query!
        print(f"{user.username}: {len(user.posts)} posts")

# ✅ GOOD: Eager loading with selectinload
from sqlalchemy.orm import selectinload

def get_users_with_posts_good(session: Session):
    statement = select(User).options(selectinload(User.posts))
    users = session.exec(statement).all()
    for user in users:
        # No additional queries
        print(f"{user.username}: {len(user.posts)} posts")
```

### Loading Strategies

```python
from sqlalchemy.orm import selectinload, joinedload, subqueryload

# Select IN loading (separate query with IN clause)
statement = select(User).options(selectinload(User.posts))

# Joined loading (LEFT OUTER JOIN)
statement = select(User).options(joinedload(User.posts))

# Subquery loading (separate query with subquery)
statement = select(User).options(subqueryload(User.posts))

# Multiple levels
statement = (
    select(User)
    .options(
        selectinload(User.posts).selectinload(Post.comments)
    )
)

# Load only specific columns
statement = select(User.id, User.username, User.email)
```

## Indexing

```python
from sqlmodel import Field, Column, Index

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Single column index
    email: str = Field(unique=True, index=True)
    username: str = Field(index=True)

    # Composite index (defined at class level)
    __table_args__ = (
        Index('ix_user_email_username', 'email', 'username'),
    )

class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    user_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(index=True)

    # Partial index (PostgreSQL)
    __table_args__ = (
        Index(
            'ix_published_posts',
            'created_at',
            postgresql_where=sa.text('published = true')
        ),
    )
```

## Bulk Operations

```python
from sqlalchemy import insert, update, delete

# Bulk insert (fastest)
def bulk_create_users(session: Session, users_data: List[dict]):
    """Insert multiple users efficiently"""
    session.execute(insert(User), users_data)
    session.commit()

# Bulk update
def bulk_update_users(session: Session, updates: List[dict]):
    """Update multiple users efficiently"""
    # Each dict must include 'id' for WHERE clause
    session.execute(update(User), updates)
    session.commit()

# Example usage
bulk_update_users(session, [
    {"id": 1, "is_active": False},
    {"id": 2, "is_active": False},
    {"id": 3, "is_active": False},
])

# Bulk delete
def bulk_delete_inactive(session: Session):
    """Delete inactive users efficiently"""
    statement = delete(User).where(User.is_active == False)
    result = session.execute(statement)
    session.commit()
    return result.rowcount
```

## Pagination Best Practices

```python
from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar('T')

class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

# Cursor-based pagination (better performance for large datasets)
def get_users_cursor(
    session: Session,
    cursor: Optional[int] = None,
    limit: int = 20
) -> List[User]:
    """Cursor-based pagination"""
    statement = select(User).order_by(User.id)

    if cursor:
        statement = statement.where(User.id > cursor)

    statement = statement.limit(limit)
    return session.exec(statement).all()

# Offset-based pagination (with total count)
def get_users_page(
    session: Session,
    page: int = 1,
    size: int = 20
) -> Page[User]:
    """Offset-based pagination with total count"""
    # Get total count efficiently
    count_statement = select(func.count()).select_from(User)
    total = session.exec(count_statement).one()

    # Get page items
    offset = (page - 1) * size
    statement = select(User).offset(offset).limit(size)
    items = session.exec(statement).all()

    return Page(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )
```

## Query Result Caching

```python
from functools import lru_cache
import redis

# In-memory caching (simple)
@lru_cache(maxsize=100)
def get_user_by_email_cached(email: str) -> Optional[User]:
    """Cache user lookups in memory"""
    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        return session.exec(statement).first()

# Redis caching
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_user_with_redis(session: Session, user_id: int) -> Optional[User]:
    """Cache user in Redis"""
    cache_key = f"user:{user_id}"

    # Try cache first
    cached = redis_client.get(cache_key)
    if cached:
        return User(**json.loads(cached))

    # Query database
    user = session.get(User, user_id)
    if user:
        # Cache for 5 minutes
        redis_client.setex(
            cache_key,
            300,
            json.dumps(user.dict())
        )

    return user

# Cache invalidation
def update_user_with_cache_invalidation(
    session: Session,
    user_id: int,
    user_data: UserUpdate
):
    """Update user and invalidate cache"""
    user = update_user(session, user_id, user_data)

    # Invalidate cache
    redis_client.delete(f"user:{user_id}")

    return user
```

## Read Replicas

```python
# Primary database (writes)
primary_engine = create_engine("postgresql://localhost/primary")

# Read replica (reads)
replica_engine = create_engine("postgresql://localhost/replica")

def get_primary_session():
    with Session(primary_engine) as session:
        yield session

def get_replica_session():
    with Session(replica_engine) as session:
        yield session

# Use in endpoints
@app.post("/users")
def create_user(
    user: UserCreate,
    session: Session = Depends(get_primary_session)
):
    # Write to primary
    return create_user(session, user)

@app.get("/users/{user_id}")
def get_user(
    user_id: int,
    session: Session = Depends(get_replica_session)
):
    # Read from replica
    return get_user(session, user_id)
```

## Database Indexes Analysis

```sql
-- PostgreSQL: Find missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
  AND n_distinct > 100
  AND correlation < 0.1;

-- Find unused indexes
SELECT schemaname, tablename, indexname
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND schemaname = 'public';

-- Index size and usage
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    idx_scan as index_scans
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;
```

## Query Performance Analysis

```python
# Enable query logging
engine = create_engine(DATABASE_URL, echo=True)

# Analyze query execution
from sqlalchemy import text

def analyze_query_performance(session: Session):
    """Analyze query execution plan (PostgreSQL)"""
    query = select(User).where(User.email.like('%example.com'))

    # Get execution plan
    explain = session.execute(
        text(f"EXPLAIN ANALYZE {str(query.compile(session.bind))}")
    )

    for row in explain:
        print(row)
```

## Batch Processing

```python
def process_users_in_batches(session: Session, batch_size: int = 1000):
    """Process large dataset in batches"""
    offset = 0

    while True:
        # Fetch batch
        statement = (
            select(User)
            .offset(offset)
            .limit(batch_size)
        )
        users = session.exec(statement).all()

        if not users:
            break

        # Process batch
        for user in users:
            # Process user
            user.processed = True
            session.add(user)

        # Commit batch
        session.commit()

        # Move to next batch
        offset += batch_size
```

## Connection Management

```python
# Check pool status
def check_pool_status(engine):
    """Monitor connection pool"""
    pool = engine.pool
    print(f"Pool size: {pool.size()}")
    print(f"Checked out: {pool.checkedout()}")
    print(f"Overflow: {pool.overflow()}")
    print(f"Checked in: {pool.checkedin()}")

# Dispose connections
def cleanup_connections(engine):
    """Close all connections"""
    engine.dispose()
```

## Compiled Query Caching

```python
from sqlalchemy import select
from sqlalchemy.sql.cache_key import CacheKey

# Enable compiled query caching (enabled by default)
engine = create_engine(
    DATABASE_URL,
    query_cache_size=1000  # Cache up to 1000 compiled queries
)
```

## Best Practices Summary

```python
# ✅ GOOD: Use indexes on frequently queried columns
class User(SQLModel, table=True):
    email: str = Field(index=True)
    created_at: datetime = Field(index=True)

# ✅ GOOD: Use eager loading to avoid N+1 queries
statement = select(User).options(selectinload(User.posts))

# ✅ GOOD: Use bulk operations for multiple inserts/updates
session.execute(insert(User), users_data)

# ✅ GOOD: Use cursor-based pagination for large datasets
statement = select(User).where(User.id > cursor).limit(20)

# ✅ GOOD: Use connection pooling
engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=40)

# ❌ BAD: Loading all relationships by default
# Configure only when needed with .options()

# ❌ BAD: Using offset pagination with large offsets
# Use cursor-based pagination instead

# ❌ BAD: Not using indexes
# Always index foreign keys and frequently queried columns
```
