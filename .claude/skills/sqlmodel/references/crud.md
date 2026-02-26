# CRUD Operations Patterns

## Create Operations

```python
from sqlmodel import Session, select
from fastapi import HTTPException

# Simple create
def create_user(session: Session, user_data: UserCreate) -> User:
    """Create a new user"""
    user = User(**user_data.dict())
    session.add(user)
    session.commit()
    session.refresh(user)  # Get auto-generated fields
    return user

# Create with validation
def create_user_with_validation(session: Session, user_data: UserCreate) -> User:
    """Create user with duplicate check"""
    # Check if username already exists
    statement = select(User).where(User.username == user_data.username)
    existing_user = session.exec(statement).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(**user_data.dict())
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# Bulk create
def create_users_bulk(session: Session, users_data: List[UserCreate]) -> List[User]:
    """Create multiple users efficiently"""
    users = [User(**user.dict()) for user in users_data]
    session.add_all(users)
    session.commit()
    for user in users:
        session.refresh(user)
    return users
```

## Read Operations

```python
# Get by ID
def get_user(session: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return session.get(User, user_id)

# Get by ID with error handling
def get_user_or_404(session: Session, user_id: int) -> User:
    """Get user by ID or raise 404"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Get by field
def get_user_by_email(session: Session, email: str) -> Optional[User]:
    """Get user by email"""
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()

# Get all
def get_users(session: Session) -> List[User]:
    """Get all users"""
    statement = select(User)
    return session.exec(statement).all()

# Get with pagination
def get_users_paginated(
    session: Session,
    skip: int = 0,
    limit: int = 100
) -> List[User]:
    """Get users with pagination"""
    statement = select(User).offset(skip).limit(limit)
    return session.exec(statement).all()

# Get with relationships
from sqlalchemy.orm import selectinload

def get_user_with_posts(session: Session, user_id: int) -> Optional[User]:
    """Get user with all posts eagerly loaded"""
    statement = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.posts))
    )
    return session.exec(statement).first()
```

## Update Operations

```python
# Full update
def update_user(session: Session, user_id: int, user_data: UserUpdate) -> User:
    """Update user with all fields"""
    user = get_user_or_404(session, user_id)

    # Update all provided fields
    for key, value in user_data.dict().items():
        setattr(user, key, value)

    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# Partial update (exclude unset fields)
def update_user_partial(
    session: Session,
    user_id: int,
    user_data: UserUpdate
) -> User:
    """Update only provided fields"""
    user = get_user_or_404(session, user_id)

    # Only update fields that were actually provided
    update_data = user_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)

    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# Update with validation
def update_user_email(
    session: Session,
    user_id: int,
    new_email: str
) -> User:
    """Update user email with uniqueness check"""
    user = get_user_or_404(session, user_id)

    # Check if email is already taken by another user
    statement = select(User).where(
        User.email == new_email,
        User.id != user_id
    )
    existing = session.exec(statement).first()

    if existing:
        raise HTTPException(status_code=400, detail="Email already in use")

    user.email = new_email
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# Bulk update
from sqlalchemy import update

def deactivate_inactive_users(session: Session, days: int = 30):
    """Deactivate users inactive for specified days"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    statement = (
        update(User)
        .where(User.last_login < cutoff_date)
        .values(is_active=False)
    )
    result = session.exec(statement)
    session.commit()
    return result.rowcount  # Number of updated rows
```

## Delete Operations

```python
# Simple delete
def delete_user(session: Session, user_id: int) -> None:
    """Delete user by ID"""
    user = get_user_or_404(session, user_id)
    session.delete(user)
    session.commit()

# Soft delete
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = None

def soft_delete_user(session: Session, user_id: int) -> User:
    """Soft delete user (mark as deleted)"""
    user = get_user_or_404(session, user_id)
    user.is_deleted = True
    user.deleted_at = datetime.utcnow()
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# Get active users only (exclude soft deleted)
def get_active_users(session: Session) -> List[User]:
    """Get only non-deleted users"""
    statement = select(User).where(User.is_deleted == False)
    return session.exec(statement).all()

# Bulk delete
from sqlalchemy import delete

def delete_old_sessions(session: Session):
    """Delete expired sessions"""
    cutoff = datetime.utcnow()
    statement = delete(Session).where(Session.expires_at < cutoff)
    result = session.exec(statement)
    session.commit()
    return result.rowcount
```

## Upsert (Insert or Update)

```python
from sqlalchemy.dialects.postgresql import insert

def upsert_user(session: Session, user_data: UserCreate) -> User:
    """Insert user or update if exists (PostgreSQL)"""
    # Create insert statement
    stmt = insert(User).values(**user_data.dict())

    # On conflict, update
    stmt = stmt.on_conflict_do_update(
        index_elements=["email"],  # Unique constraint column
        set_=user_data.dict()
    )

    result = session.execute(stmt)
    session.commit()

    # Fetch the user
    user = get_user_by_email(session, user_data.email)
    return user

# Alternative: Manual upsert
def upsert_user_manual(session: Session, user_data: UserCreate) -> User:
    """Manual upsert logic"""
    # Try to find existing user
    user = get_user_by_email(session, user_data.email)

    if user:
        # Update existing
        for key, value in user_data.dict().items():
            setattr(user, key, value)
    else:
        # Create new
        user = User(**user_data.dict())
        session.add(user)

    session.commit()
    session.refresh(user)
    return user
```

## Transaction Patterns

```python
from sqlalchemy.exc import SQLAlchemyError

def transfer_with_transaction(
    session: Session,
    from_user_id: int,
    to_user_id: int,
    amount: Decimal
):
    """Transfer funds between users with transaction"""
    try:
        # Start nested transaction
        from_user = get_user_or_404(session, from_user_id)
        to_user = get_user_or_404(session, to_user_id)

        if from_user.balance < amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")

        # Perform transfer
        from_user.balance -= amount
        to_user.balance += amount

        session.add(from_user)
        session.add(to_user)
        session.commit()

        return {"success": True, "amount": amount}

    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
```

## FastAPI Integration Patterns

```python
from fastapi import FastAPI, Depends, HTTPException, status
from sqlmodel import Session

app = FastAPI()

# CREATE
@app.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(
    user: UserCreate,
    session: Session = Depends(get_session)
):
    return create_user(session, user)

# READ - Single
@app.get("/users/{user_id}", response_model=UserRead)
def get_user_endpoint(
    user_id: int,
    session: Session = Depends(get_session)
):
    user = get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# READ - List
@app.get("/users", response_model=List[UserRead])
def list_users_endpoint(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    return get_users_paginated(session, skip, limit)

# UPDATE
@app.put("/users/{user_id}", response_model=UserRead)
def update_user_endpoint(
    user_id: int,
    user: UserUpdate,
    session: Session = Depends(get_session)
):
    return update_user_partial(session, user_id, user)

# DELETE
@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_endpoint(
    user_id: int,
    session: Session = Depends(get_session)
):
    delete_user(session, user_id)
    return None
```
