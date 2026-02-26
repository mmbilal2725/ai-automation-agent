# Query Patterns and Filtering

## Basic Queries

```python
from sqlmodel import select, Session

# Select all
def get_all_users(session: Session) -> List[User]:
    statement = select(User)
    return session.exec(statement).all()

# Select one
def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
    statement = select(User).where(User.id == user_id)
    return session.exec(statement).first()

# Select with scalar result
def get_user_scalar(session: Session, user_id: int) -> Optional[User]:
    statement = select(User).where(User.id == user_id)
    return session.exec(statement).one_or_none()
```

## Where Clauses

```python
from sqlmodel import select, or_, and_, not_

# Simple equality
statement = select(User).where(User.username == "john")

# Not equal
statement = select(User).where(User.status != "banned")

# Multiple conditions (AND)
statement = select(User).where(
    User.is_active == True,
    User.age >= 18
)

# OR conditions
statement = select(User).where(
    or_(
        User.role == "admin",
        User.role == "moderator"
    )
)

# AND + OR combination
statement = select(User).where(
    and_(
        User.is_active == True,
        or_(
            User.role == "admin",
            User.role == "moderator"
        )
    )
)

# NOT condition
statement = select(User).where(not_(User.is_deleted))

# IN clause
user_ids = [1, 2, 3, 4]
statement = select(User).where(User.id.in_(user_ids))

# NOT IN clause
statement = select(User).where(User.id.not_in(user_ids))

# LIKE pattern matching
statement = select(User).where(User.email.like("%@example.com"))

# ILIKE (case-insensitive, PostgreSQL)
statement = select(User).where(User.username.ilike("%john%"))

# BETWEEN
statement = select(User).where(User.age.between(18, 65))

# IS NULL
statement = select(User).where(User.deleted_at.is_(None))

# IS NOT NULL
statement = select(User).where(User.deleted_at.is_not(None))
```

## Ordering

```python
# Order by single column
statement = select(User).order_by(User.created_at)

# Order descending
statement = select(User).order_by(User.created_at.desc())

# Multiple order by
statement = select(User).order_by(
    User.is_active.desc(),
    User.username.asc()
)
```

## Pagination

```python
# Offset and limit
def get_users_page(session: Session, page: int = 1, page_size: int = 20):
    offset = (page - 1) * page_size
    statement = select(User).offset(offset).limit(page_size)
    users = session.exec(statement).all()

    # Get total count
    count_statement = select(func.count()).select_from(User)
    total = session.exec(count_statement).one()

    return {
        "items": users,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }
```

## Aggregations

```python
from sqlalchemy import func, select

# Count
def count_users(session: Session) -> int:
    statement = select(func.count()).select_from(User)
    return session.exec(statement).one()

# Count with filter
def count_active_users(session: Session) -> int:
    statement = (
        select(func.count())
        .select_from(User)
        .where(User.is_active == True)
    )
    return session.exec(statement).one()

# Sum
def total_balance(session: Session) -> Decimal:
    statement = select(func.sum(User.balance))
    return session.exec(statement).one() or Decimal(0)

# Average
def average_age(session: Session) -> float:
    statement = select(func.avg(User.age))
    return session.exec(statement).one()

# Min/Max
def age_range(session: Session):
    statement = select(
        func.min(User.age),
        func.max(User.age)
    )
    min_age, max_age = session.exec(statement).one()
    return {"min": min_age, "max": max_age}
```

## Group By

```python
# Group by with count
def users_by_role(session: Session):
    statement = (
        select(User.role, func.count(User.id))
        .group_by(User.role)
    )
    return session.exec(statement).all()

# Group by with having
def active_roles(session: Session):
    """Get roles with at least 5 active users"""
    statement = (
        select(User.role, func.count(User.id))
        .where(User.is_active == True)
        .group_by(User.role)
        .having(func.count(User.id) >= 5)
    )
    return session.exec(statement).all()
```

## Joins

```python
# Inner join
statement = (
    select(User, Post)
    .join(Post, User.id == Post.user_id)
)
results = session.exec(statement).all()

# Left outer join
statement = (
    select(User, Post)
    .outerjoin(Post, User.id == Post.user_id)
)

# Join with filter
statement = (
    select(User, Post)
    .join(Post)
    .where(Post.published == True)
)

# Multiple joins
statement = (
    select(User, Post, Comment)
    .join(Post, User.id == Post.user_id)
    .join(Comment, Post.id == Comment.post_id)
)
```

## Subqueries

```python
# Scalar subquery
from sqlalchemy import ScalarSelect

# Get users with post count
post_count_subq = (
    select(func.count(Post.id))
    .where(Post.user_id == User.id)
    .scalar_subquery()
)

statement = select(User, post_count_subq.label("post_count"))
results = session.exec(statement).all()

# Correlated subquery
# Get users who have published posts
published_subq = (
    select(Post.user_id)
    .where(Post.published == True)
    .distinct()
)

statement = select(User).where(User.id.in_(published_subq))
users = session.exec(statement).all()
```

## Dynamic Filtering

```python
from typing import Optional

def get_users_filtered(
    session: Session,
    username: Optional[str] = None,
    email: Optional[str] = None,
    is_active: Optional[bool] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None
) -> List[User]:
    """Get users with dynamic filters"""
    statement = select(User)

    # Add filters dynamically
    if username:
        statement = statement.where(User.username.ilike(f"%{username}%"))

    if email:
        statement = statement.where(User.email == email)

    if is_active is not None:
        statement = statement.where(User.is_active == is_active)

    if min_age is not None:
        statement = statement.where(User.age >= min_age)

    if max_age is not None:
        statement = statement.where(User.age <= max_age)

    return session.exec(statement).all()

# FastAPI endpoint with filters
@app.get("/users/search", response_model=List[UserRead])
def search_users(
    username: Optional[str] = None,
    email: Optional[str] = None,
    is_active: Optional[bool] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    session: Session = Depends(get_session)
):
    return get_users_filtered(
        session,
        username=username,
        email=email,
        is_active=is_active,
        min_age=min_age,
        max_age=max_age
    )
```

## Text Search (PostgreSQL)

```python
from sqlalchemy import func, text

# Full-text search
def search_posts(session: Session, query: str):
    """Full-text search on posts"""
    statement = (
        select(Post)
        .where(
            func.to_tsvector('english', Post.title + ' ' + Post.content)
            .match(query)
        )
    )
    return session.exec(statement).all()

# Raw SQL for complex searches
def advanced_search(session: Session, query: str):
    """Advanced full-text search with ranking"""
    sql = text("""
        SELECT *,
               ts_rank(
                   to_tsvector('english', title || ' ' || content),
                   plainto_tsquery('english', :query)
               ) as rank
        FROM post
        WHERE to_tsvector('english', title || ' ' || content) @@
              plainto_tsquery('english', :query)
        ORDER BY rank DESC
    """)
    result = session.execute(sql, {"query": query})
    return result.all()
```

## JSON Queries (PostgreSQL)

```python
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import cast

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    metadata: Dict[str, Any] = Field(sa_column=Column(JSONB))

# Query JSON field
def get_products_by_category(session: Session, category: str):
    """Get products by category in JSON field"""
    statement = select(Product).where(
        Product.metadata["category"].astext == category
    )
    return session.exec(statement).all()

# JSON contains
def get_products_with_tag(session: Session, tag: str):
    """Get products with specific tag in JSON array"""
    statement = select(Product).where(
        Product.metadata["tags"].contains([tag])
    )
    return session.exec(statement).all()
```

## Window Functions

```python
from sqlalchemy import func, over

# Row number
def get_ranked_users(session: Session):
    """Get users with ranking by score"""
    row_number = func.row_number().over(
        order_by=User.score.desc()
    ).label("rank")

    statement = select(User, row_number)
    return session.exec(statement).all()

# Partition by
def get_top_user_per_team(session: Session):
    """Get highest scoring user in each team"""
    rank = func.rank().over(
        partition_by=User.team_id,
        order_by=User.score.desc()
    ).label("team_rank")

    subq = select(User, rank).subquery()

    statement = select(subq).where(subq.c.team_rank == 1)
    return session.exec(statement).all()
```

## Distinct and Unique

```python
# Distinct
statement = select(User.role).distinct()
roles = session.exec(statement).all()

# Distinct on specific columns (PostgreSQL)
from sqlalchemy import distinct

statement = select(User).distinct(User.email)
users = session.exec(statement).all()
```

## Exists

```python
# Check if record exists
def user_exists(session: Session, email: str) -> bool:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first() is not None

# Using exists() for better performance
from sqlalchemy import exists

def user_exists_efficient(session: Session, email: str) -> bool:
    statement = select(exists().where(User.email == email))
    return session.exec(statement).one()
```
