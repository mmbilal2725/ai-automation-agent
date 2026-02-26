# FastAPI Project Structure

## Overview

For larger applications, organizing code across multiple files improves maintainability and scalability. FastAPI provides `APIRouter` for modular organization.

## Basic Structure

```
app/
├── __init__.py
├── main.py
├── dependencies.py
├── config.py
├── models.py
├── routers/
│   ├── __init__.py
│   ├── users.py
│   ├── items.py
│   └── auth.py
├── services/
│   ├── __init__.py
│   ├── user_service.py
│   └── item_service.py
├── database/
│   ├── __init__.py
│   ├── db.py
│   └── models.py
└── tests/
    ├── __init__.py
    ├── test_users.py
    └── test_items.py
```

## APIRouter Basics

### Creating a Router

```python
# app/routers/users.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/users/")
async def read_users():
    return [{"username": "Rick"}, {"username": "Morty"}]

@router.get("/users/me")
async def read_user_me():
    return {"username": "current_user"}

@router.get("/users/{username}")
async def read_user(username: str):
    return {"username": username}
```

### Router with Prefix and Tags

```python
# app/routers/items.py
from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix="/items",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def read_items():
    return [{"name": "Item 1"}, {"name": "Item 2"}]

@router.get("/{item_id}")
async def read_item(item_id: int):
    if item_id == 99:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id, "name": f"Item {item_id}"}

@router.post("/")
async def create_item(name: str):
    return {"name": name}
```

### Including Routers in Main App

```python
# app/main.py
from fastapi import FastAPI
from .routers import users, items, auth

app = FastAPI()

# Include routers
app.include_router(users.router)
app.include_router(items.router)
app.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

## Shared Dependencies

### Define Dependencies

```python
# app/dependencies.py
from typing import Annotated
from fastapi import Header, HTTPException

async def get_token_header(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")

async def get_query_token(token: str):
    if token != "jessica":
        raise HTTPException(status_code=400, detail="No Jessica token provided")
```

### Use in Routers

```python
# app/routers/items.py
from fastapi import APIRouter, Depends
from ..dependencies import get_token_header

router = APIRouter(
    prefix="/items",
    tags=["items"],
    dependencies=[Depends(get_token_header)],
)

@router.get("/")
async def read_items():
    return [{"name": "Item 1"}]
```

### Global Dependencies

```python
# app/main.py
from fastapi import Depends, FastAPI
from .dependencies import get_query_token

app = FastAPI(dependencies=[Depends(get_query_token)])
```

## Production Structure

### Complete Example

```
app/
├── __init__.py
├── main.py                 # FastAPI app instance
├── config.py               # Settings and configuration
├── dependencies.py         # Shared dependencies
│
├── api/                    # API layer
│   ├── __init__.py
│   ├── deps.py            # API-specific dependencies
│   └── v1/                # API versioning
│       ├── __init__.py
│       ├── api.py         # API router aggregator
│       └── endpoints/
│           ├── __init__.py
│           ├── users.py
│           ├── items.py
│           ├── auth.py
│           └── admin.py
│
├── core/                   # Core functionality
│   ├── __init__.py
│   ├── config.py          # Settings class
│   ├── security.py        # Security utilities
│   └── exceptions.py      # Custom exceptions
│
├── models/                 # Database models
│   ├── __init__.py
│   ├── user.py
│   ├── item.py
│   └── team.py
│
├── schemas/                # Pydantic models
│   ├── __init__.py
│   ├── user.py
│   ├── item.py
│   └── token.py
│
├── services/               # Business logic
│   ├── __init__.py
│   ├── user_service.py
│   ├── item_service.py
│   └── auth_service.py
│
├── database/               # Database configuration
│   ├── __init__.py
│   ├── base.py            # SQLModel base
│   ├── session.py         # Session management
│   └── init_db.py         # Database initialization
│
└── tests/
    ├── __init__.py
    ├── conftest.py        # Pytest fixtures
    ├── api/
    │   ├── __init__.py
    │   └── v1/
    │       ├── test_users.py
    │       └── test_items.py
    └── services/
        ├── __init__.py
        └── test_user_service.py
```

### main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.database.session import engine
from app.models import SQLModel

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Create tables on startup
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}
```

### config.py

```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "My FastAPI Project"
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: str

    BACKEND_CORS_ORIGINS: List[str] = []

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### api/v1/api.py (Router Aggregator)

```python
from fastapi import APIRouter
from app.api.v1.endpoints import users, items, auth, admin

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
```

### api/v1/endpoints/users.py

```python
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.api.deps import get_current_user, get_session
from app.models.user import User
from app.schemas.user import UserCreate, UserPublic, UserUpdate
from app.services.user_service import UserService

router = APIRouter()

@router.get("/", response_model=list[UserPublic])
def read_users(
    session: Annotated[Session, Depends(get_session)],
    skip: int = 0,
    limit: int = 100,
):
    service = UserService(session)
    users = service.get_users(skip=skip, limit=limit)
    return users

@router.get("/me", response_model=UserPublic)
def read_user_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    return current_user

@router.get("/{user_id}", response_model=UserPublic)
def read_user(
    user_id: int,
    session: Annotated[Session, Depends(get_session)],
):
    service = UserService(session)
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=UserPublic)
def create_user(
    user: UserCreate,
    session: Annotated[Session, Depends(get_session)],
):
    service = UserService(session)
    return service.create_user(user)

@router.patch("/{user_id}", response_model=UserPublic)
def update_user(
    user_id: int,
    user: UserUpdate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    service = UserService(session)
    return service.update_user(user_id, user)
```

### services/user_service.py

```python
from sqlmodel import Session, select
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash

class UserService:
    def __init__(self, session: Session):
        self.session = session

    def get_users(self, skip: int = 0, limit: int = 100):
        return self.session.exec(
            select(User).offset(skip).limit(limit)
        ).all()

    def get_user(self, user_id: int):
        return self.session.get(User, user_id)

    def get_user_by_email(self, email: str):
        return self.session.exec(
            select(User).where(User.email == email)
        ).first()

    def create_user(self, user: UserCreate):
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email,
            hashed_password=hashed_password,
            full_name=user.full_name
        )
        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return db_user

    def update_user(self, user_id: int, user: UserUpdate):
        db_user = self.get_user(user_id)
        if not db_user:
            return None

        user_data = user.model_dump(exclude_unset=True)
        if "password" in user_data:
            hashed_password = get_password_hash(user_data["password"])
            del user_data["password"]
            user_data["hashed_password"] = hashed_password

        db_user.sqlmodel_update(user_data)
        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return db_user
```

## API Versioning

### URL Path Versioning

```python
# app/api/v1/api.py
from fastapi import APIRouter
api_v1_router = APIRouter()

# app/api/v2/api.py
api_v2_router = APIRouter()

# app/main.py
app.include_router(api_v1_router, prefix="/api/v1")
app.include_router(api_v2_router, prefix="/api/v2")
```

### Header Versioning

```python
from fastapi import Header, HTTPException

async def get_api_version(
    accept_version: str | None = Header(default="v1", alias="Accept-Version")
):
    if accept_version not in ["v1", "v2"]:
        raise HTTPException(status_code=400, detail="Unsupported API version")
    return accept_version

@app.get("/items/")
async def read_items(version: str = Depends(get_api_version)):
    if version == "v1":
        return {"version": "v1", "items": []}
    return {"version": "v2", "items": []}
```

## Sub-Applications (Mounts)

```python
from fastapi import FastAPI

app = FastAPI()
api_app = FastAPI()
admin_app = FastAPI()

@api_app.get("/items/")
async def read_items():
    return [{"item": "Foo"}]

@admin_app.get("/users/")
async def read_users():
    return [{"user": "Admin"}]

app.mount("/api", api_app)
app.mount("/admin", admin_app)
```

URLs:
- `/api/items/` → API items
- `/admin/users/` → Admin users

## Best Practices

1. **Use APIRouter** for modular organization
2. **Separate concerns** - routers, services, models, schemas
3. **Version your API** for backward compatibility
4. **Use services layer** for business logic
5. **Keep routers thin** - delegate to services
6. **Group related endpoints** in same router
7. **Use dependencies** for shared logic
8. **Document with tags** for better API docs
9. **Configure CORS** appropriately
10. **Use environment variables** for configuration
