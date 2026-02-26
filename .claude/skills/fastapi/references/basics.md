# FastAPI Basics

## Installation

```bash
pip install "fastapi[standard]"
```

This installs FastAPI with all standard dependencies including uvicorn server.

## Hello World

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

**Run the server:**
```bash
fastapi dev main.py
```

Access:
- Application: http://127.0.0.1:8000
- Interactive docs (Swagger UI): http://127.0.0.1:8000/docs
- Alternative docs (ReDoc): http://127.0.0.1:8000/redoc
- OpenAPI schema: http://127.0.0.1:8000/openapi.json

## Path Parameters

```python
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
```

**Features:**
- Type conversion: `item_id` automatically converted to `int`
- Validation: Returns error if type conversion fails
- Documentation: Automatically added to OpenAPI schema

### Path Parameters with Enums

```python
from enum import Enum

class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}
    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}
    return {"model_name": model_name, "message": "Have some residuals"}
```

## Query Parameters

```python
from typing import Union

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]

@app.get("/items/")
async def read_items(skip: int = 0, limit: int = 10, q: Union[str, None] = None):
    if q:
        return {"items": fake_items_db[skip : skip + limit], "q": q}
    return {"items": fake_items_db[skip : skip + limit]}
```

**Key points:**
- Optional parameters with defaults: `skip: int = 0`
- Optional parameters without defaults: `q: Union[str, None] = None` or `q: str | None = None`
- Boolean parameters: `short: bool = False`

### Query Parameter Validation

```python
from typing import Annotated
from fastapi import Query

@app.get("/items/")
async def read_items(
    q: Annotated[str | None, Query(min_length=3, max_length=50)] = None
):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results
```

**Validation options:**
- `min_length`, `max_length`: String length
- `pattern`: Regex pattern (e.g., `pattern="^fixedquery$"`)
- `ge`, `le`, `gt`, `lt`: Numeric comparisons (greater/less than or equal)
- `alias`: Different name in query string
- `deprecated`: Mark parameter as deprecated
- `include_in_schema`: Exclude from OpenAPI docs

### Multiple Values

```python
@app.get("/items/")
async def read_items(q: Annotated[list[str] | None, Query()] = None):
    return {"q": q}
```

URL: `/items/?q=foo&q=bar` → `{"q": ["foo", "bar"]}`

## Request Body

Use Pydantic models for request bodies:

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

@app.post("/items/")
async def create_item(item: Item):
    item_dict = item.model_dump()
    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    return item_dict
```

**Automatic features:**
- JSON validation
- Type conversion
- Error messages for invalid data
- OpenAPI schema generation
- Editor autocomplete for `item.` attributes

### Field Validation

```python
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    price: float = Field(..., gt=0)
    tax: float | None = Field(None, ge=0)
```

### Nested Models

```python
from pydantic import BaseModel

class Image(BaseModel):
    url: str
    name: str

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    tags: list[str] = []
    images: list[Image] | None = None

@app.post("/items/")
async def create_item(item: Item):
    return item
```

## Path Parameters and Request Body Together

```python
@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item, q: str | None = None):
    result = {"item_id": item_id, **item.model_dump()}
    if q:
        result.update({"q": q})
    return result
```

FastAPI recognizes:
- Path parameters: `item_id` (from path)
- Request body: `item` (Pydantic model)
- Query parameters: `q` (not in path, not a model)

## Response Model

```python
from pydantic import BaseModel, EmailStr

class UserIn(BaseModel):
    username: str
    password: str
    email: EmailStr
    full_name: str | None = None

class UserOut(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None

@app.post("/user/", response_model=UserOut)
async def create_user(user: UserIn):
    return user
```

**Benefits:**
- Output validation and serialization
- Automatic filtering of sensitive data (password not included in response)
- OpenAPI documentation shows response schema

## Status Codes

```python
from fastapi import status

@app.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(item: Item):
    return item
```

Common status codes:
- `200` - OK (default for GET)
- `201` - Created (POST)
- `204` - No Content (DELETE)
- `400` - Bad Request
- `404` - Not Found
- `422` - Unprocessable Entity (validation error)

## Form Data

```python
from typing import Annotated
from fastapi import Form

@app.post("/login/")
async def login(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()]
):
    return {"username": username}
```

**Important:** Install `python-multipart` first:
```bash
pip install python-multipart
```

## File Uploads

```python
from typing import Annotated
from fastapi import File, UploadFile

@app.post("/files/")
async def create_file(file: Annotated[bytes, File()]):
    return {"file_size": len(file)}

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    contents = await file.read()
    return {"filename": file.filename, "size": len(contents)}
```

**UploadFile attributes:**
- `filename`: Original file name
- `content_type`: MIME type
- `file`: Actual file object
- `read()`: Read file contents
- `write()`: Write to file
- `seek()`: Go to position in file

## Error Handling

```python
from fastapi import HTTPException

items = {"foo": "The Foo Wrestlers"}

@app.get("/items/{item_id}")
async def read_item(item_id: str):
    if item_id not in items:
        raise HTTPException(
            status_code=404,
            detail="Item not found",
            headers={"X-Error": "Custom header"}
        )
    return {"item": items[item_id]}
```

## Additional Data Types

FastAPI supports many Python types:

```python
from datetime import datetime, time, timedelta
from uuid import UUID
from pydantic import HttpUrl

@app.put("/items/{item_id}")
async def read_items(
    item_id: UUID,
    start_datetime: datetime,
    end_datetime: datetime,
    process_after: timedelta,
    repeat_at: time | None = None,
    url: HttpUrl | None = None,
):
    return {
        "item_id": item_id,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "process_after": process_after,
        "repeat_at": repeat_at,
        "url": url,
    }
```

Supported types:
- `UUID`, `datetime`, `date`, `time`, `timedelta`
- `bytes`, `Decimal`, `frozenset`
- `HttpUrl`, `EmailStr`, `IPvAnyAddress`
- `FilePath`, `DirectoryPath`

## Headers and Cookies

```python
from typing import Annotated
from fastapi import Cookie, Header

@app.get("/items/")
async def read_items(
    user_agent: Annotated[str | None, Header()] = None,
    session_id: Annotated[str | None, Cookie()] = None
):
    return {"User-Agent": user_agent, "session_id": session_id}
```

**Note:** Header parameter names are automatically converted:
- Python: `user_agent` (snake_case)
- HTTP: `User-Agent` (with hyphens)

## Response Headers and Cookies

```python
from fastapi import Response

@app.post("/cookie/")
async def create_cookie(response: Response):
    response.set_cookie(key="session_id", value="abc123")
    return {"message": "Cookie set"}

@app.get("/headers/")
async def get_headers(response: Response):
    response.headers["X-Custom-Header"] = "Custom value"
    return {"message": "Check headers"}
```
