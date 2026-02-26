# FastAPI Security

## Overview

FastAPI provides built-in security utilities for authentication and authorization based on OpenAPI standards. This includes OAuth2, JWT tokens, API keys, and HTTP authentication.

## OAuth2 with Password Flow

### Basic Setup

```python
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    # Validate credentials
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": user.username, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}
```

**What happens:**
1. User sends username/password to `/token`
2. Server validates and returns access token
3. Client sends token in `Authorization: Bearer <token>` header
4. `oauth2_scheme` extracts and validates token

### OAuth2PasswordRequestForm Fields

- `username`: str
- `password`: str
- `scope`: str (optional, space-separated)
- `grant_type`: str (optional)
- `client_id`: str (optional)
- `client_secret`: str (optional)

## JWT Tokens (Production-Ready)

### Installation

```bash
pip install "python-jose[cryptography]" "passlib[bcrypt]"
```

### Complete Implementation

```python
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel

# Configuration
SECRET_KEY = "your-secret-key-keep-it-secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

# Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str

# Fake database
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(username: str):
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return UserInDB(**user_dict)

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Endpoints
@app.post("/token")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@app.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user

@app.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]
```

### Password Hashing

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash a password
hashed = pwd_context.hash("secret123")

# Verify a password
is_valid = pwd_context.verify("secret123", hashed)
```

### JWT Token Creation and Validation

```python
import jwt
from datetime import datetime, timedelta, timezone

# Create token
data = {"sub": "username", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
token = jwt.encode(data, SECRET_KEY, algorithm="HS256")

# Decode token
try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    username = payload.get("sub")
except jwt.InvalidTokenError:
    # Handle invalid token
    pass
```

## OAuth2 Scopes (Permissions)

```python
from fastapi import Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "items:read": "Read items",
        "items:write": "Write items",
        "users:read": "Read users",
        "users:write": "Write users"
    }
)

async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)]
):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(scopes=token_scopes, username=username)
    except InvalidTokenError:
        raise credentials_exception

    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception

    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )

    return user

@app.get("/items/", dependencies=[Security(get_current_user, scopes=["items:read"])])
async def read_items():
    return [{"item_id": "Foo"}]

@app.post("/items/", dependencies=[Security(get_current_user, scopes=["items:write"])])
async def create_item(item: Item):
    return item
```

## HTTP Basic Auth

```python
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

app = FastAPI()
security = HTTPBasic()

def get_current_username(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
):
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = b"stanleyjobson"
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = b"swordfish"
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/users/me")
def read_current_user(username: Annotated[str, Depends(get_current_username)]):
    return {"username": username}
```

**Note:** Use `secrets.compare_digest()` to prevent timing attacks.

## API Key Authentication

### Header-based API Key

```python
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY = "your-api-key"
api_key_header = APIKeyHeader(name="X-API-Key")

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return api_key

@app.get("/items/")
async def read_items(api_key: str = Depends(get_api_key)):
    return [{"item": "Foo"}]
```

### Query Parameter API Key

```python
from fastapi.security import APIKeyQuery

api_key_query = APIKeyQuery(name="api_key")

async def get_api_key(api_key: str = Security(api_key_query)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return api_key
```

### Cookie-based API Key

```python
from fastapi.security import APIKeyCookie

api_key_cookie = APIKeyCookie(name="session")

async def get_api_key(api_key: str = Security(api_key_cookie)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return api_key
```

## CORS (Cross-Origin Resource Sharing)

```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Parameters:**
- `allow_origins`: List of allowed origins (use `["*"]` for all)
- `allow_credentials`: Allow cookies/authentication
- `allow_methods`: Allowed HTTP methods
- `allow_headers`: Allowed headers
- `expose_headers`: Headers exposed to browser
- `max_age`: Cache preflight responses (seconds)

## Best Practices

1. **Never commit SECRET_KEY** - Use environment variables
2. **Use HTTPS in production** - Tokens sent in headers need encryption
3. **Set appropriate token expiration** - Balance security and UX
4. **Hash passwords** - Never store plain text passwords
5. **Use timing-safe comparisons** - `secrets.compare_digest()` for credentials
6. **Implement refresh tokens** - For long-lived sessions
7. **Validate token claims** - Check `exp`, `iss`, `aud` etc.
8. **Rate limit authentication** - Prevent brute force attacks
9. **Log authentication events** - Monitor for suspicious activity
10. **Use OAuth2 scopes** - Implement least-privilege access

## Environment Variables for Secrets

```python
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
```

**.env file:**
```
SECRET_KEY=your-super-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
```
