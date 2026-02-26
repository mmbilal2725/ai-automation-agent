# FastAPI Dependencies

## Overview

Dependencies in FastAPI provide a powerful dependency injection system for:
- Shared logic and code reuse
- Database connections
- Security and authentication
- Configuration management
- Minimizing code duplication

## Basic Dependency

### Creating a Dependency

```python
from typing import Annotated
from fastapi import Depends, FastAPI

app = FastAPI()

async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}
```

### Using the Dependency

```python
@app.get("/items/")
async def read_items(commons: Annotated[dict, Depends(common_parameters)]):
    return commons

@app.get("/users/")
async def read_users(commons: Annotated[dict, Depends(common_parameters)]):
    return commons
```

**What happens:**
1. FastAPI calls `common_parameters` with correct parameters from request
2. Result is passed to path operation function as `commons`
3. Parameters are validated and documented in OpenAPI

## Type Aliases for Reusability

Instead of repeating `Annotated[dict, Depends(common_parameters)]`:

```python
CommonsDep = Annotated[dict, Depends(common_parameters)]

@app.get("/items/")
async def read_items(commons: CommonsDep):
    return commons

@app.get("/users/")
async def read_users(commons: CommonsDep):
    return commons
```

## Classes as Dependencies

```python
from typing import Annotated

class CommonQueryParams:
    def __init__(self, q: str | None = None, skip: int = 0, limit: int = 100):
        self.q = q
        self.skip = skip
        self.limit = limit

CommonsDep = Annotated[CommonQueryParams, Depends()]

@app.get("/items/")
async def read_items(commons: CommonsDep):
    response = {}
    if commons.q:
        response.update({"q": commons.q})
    items = fake_items_db[commons.skip : commons.skip + commons.limit]
    response.update({"items": items})
    return response
```

**Note:** `Depends()` without arguments uses the type annotation as the dependency.

## Sub-dependencies

Dependencies can have their own dependencies:

```python
from fastapi import Cookie

def query_extractor(q: str | None = None):
    return q

def query_or_cookie_extractor(
    q: Annotated[str, Depends(query_extractor)],
    last_query: Annotated[str | None, Cookie()] = None,
):
    if not q:
        return last_query
    return q

@app.get("/items/")
async def read_query(
    query_or_default: Annotated[str, Depends(query_or_cookie_extractor)]
):
    return {"q_or_cookie": query_or_default}
```

**Dependency tree:**
```
read_query
    └── query_or_cookie_extractor
            ├── query_extractor
            └── last_query (Cookie)
```

## Dependencies in Path Operation Decorators

For dependencies that don't return a value (e.g., verification):

```python
from fastapi import Header, HTTPException

async def verify_token(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")

async def verify_key(x_key: Annotated[str, Header()]):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key

@app.get("/items/", dependencies=[Depends(verify_token), Depends(verify_key)])
async def read_items():
    return [{"item": "Portal Gun"}, {"item": "Plumbus"}]
```

**Use case:** Dependencies that perform actions but don't need to return values.

## Global Dependencies

Apply dependencies to all path operations:

```python
app = FastAPI(dependencies=[Depends(verify_token), Depends(verify_key)])
```

## Dependencies with Yield

For setup and teardown (e.g., database sessions):

```python
async def get_db():
    db = DBSession()
    try:
        yield db
    finally:
        db.close()

@app.get("/items/")
async def read_items(db: Annotated[DBSession, Depends(get_db)]):
    items = db.query(Item).all()
    return items
```

**Execution flow:**
1. Code before `yield` runs before request processing
2. `yield`ed value is injected into path operation
3. Code after `yield` runs after response is sent

### Database Session Example

```python
from sqlmodel import Session, create_engine

engine = create_engine("sqlite:///database.db")

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

@app.get("/heroes/")
def read_heroes(session: SessionDep):
    heroes = session.exec(select(Hero)).all()
    return heroes
```

### Context Manager Style

```python
class DBSession:
    def __enter__(self):
        self.db = connect_to_database()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

async def get_db():
    with DBSession() as db:
        yield db
```

## Dependency Caching

By default, dependencies are cached within a single request:

```python
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    # Expensive operation
    user = decode_token(token)
    return user

@app.get("/items/")
async def read_items(
    user1: Annotated[User, Depends(get_current_user)],
    user2: Annotated[User, Depends(get_current_user)]
):
    # get_current_user called only once
    return {"user1": user1, "user2": user2}
```

### Disable Caching

```python
@app.get("/items/")
async def read_items(
    user: Annotated[User, Depends(get_current_user, use_cache=False)]
):
    return user
```

## Advanced Patterns

### Parameterized Dependencies

```python
def pagination(skip: int = 0, limit: int = 100):
    def paginate(items: list):
        return items[skip : skip + limit]
    return paginate

@app.get("/items/")
async def read_items(paginate: Annotated[callable, Depends(pagination)]):
    items = get_all_items()
    return paginate(items)
```

### Dependency Override (Testing)

```python
async def override_get_db():
    return MockDB()

app.dependency_overrides[get_db] = override_get_db
```

**Use case:** Replace real dependencies with mocks during testing.

## Common Use Cases

### 1. Authentication Dependency

```python
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user

@app.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
```

### 2. Permission Checks

```python
async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_admin_user(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

@app.delete("/items/{item_id}")
async def delete_item(
    item_id: int,
    admin: Annotated[User, Depends(get_admin_user)]
):
    return {"message": "Item deleted"}
```

**Dependency chain:**
```
get_admin_user → get_current_active_user → get_current_user → oauth2_scheme
```

### 3. Configuration Dependency

```python
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "FastAPI App"
    admin_email: str
    database_url: str

@lru_cache()
def get_settings():
    return Settings()

@app.get("/info")
async def info(settings: Annotated[Settings, Depends(get_settings)]):
    return {
        "app_name": settings.app_name,
        "admin_email": settings.admin_email
    }
```

**Note:** `@lru_cache()` ensures settings are loaded only once.

## Best Practices

1. **Use type aliases** for commonly used dependencies
2. **Keep dependencies focused** on single responsibilities
3. **Use yield** for resources requiring cleanup
4. **Cache expensive operations** (default behavior)
5. **Override for testing** using `dependency_overrides`
6. **Chain dependencies** for progressive validation/transformation
