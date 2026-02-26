# FastAPI Advanced Topics

## Background Tasks

Execute tasks after returning a response (e.g., sending emails, processing data).

```python
from fastapi import BackgroundTasks

def write_log(message: str):
    with open("log.txt", "a") as log:
        log.write(f"{message}\n")

def send_email(email: str, message: str):
    # Simulate sending email
    import time
    time.sleep(3)
    print(f"Email sent to {email}: {message}")

@app.post("/send-notification/")
async def send_notification(
    email: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(send_email, email, "Welcome!")
    background_tasks.add_task(write_log, f"Email queued for {email}")
    return {"message": "Notification sent in the background"}
```

**Key points:**
- Response returned immediately
- Tasks execute after response sent
- Multiple tasks can be added
- Tasks execute sequentially

## Middleware

Process requests and responses globally.

### Custom Middleware

```python
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

### Built-in Middleware

```python
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["example.com", "*.example.com"]
)
```

### Logging Middleware

```python
import logging

logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response
```

## WebSockets

Real-time bidirectional communication.

```python
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")
```

### Connection Manager (Multiple Clients)

```python
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")
```

## Lifespan Events

Execute code on application startup/shutdown.

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    # Load ML model, initialize database, etc.
    ml_model = load_ml_model()
    yield {"ml_model": ml_model}
    # Shutdown
    print("Shutting down...")
    # Cleanup resources

app = FastAPI(lifespan=lifespan)

@app.get("/predict/")
async def predict(request: Request):
    ml_model = request.state.ml_model
    result = ml_model.predict(data)
    return {"prediction": result}
```

### Legacy Event Handlers

```python
@app.on_event("startup")
async def startup_event():
    print("Application starting up")
    # Initialize database, load models, etc.

@app.on_event("shutdown")
async def shutdown_event():
    print("Application shutting down")
    # Close database connections, cleanup, etc.
```

## Custom Response Types

### HTML Response

```python
from fastapi.responses import HTMLResponse

@app.get("/html", response_class=HTMLResponse)
async def get_html():
    return """
    <html>
        <head><title>FastAPI</title></head>
        <body><h1>Hello World</h1></body>
    </html>
    """
```

### File Response

```python
from fastapi.responses import FileResponse

@app.get("/download")
async def download_file():
    return FileResponse(
        path="file.pdf",
        filename="download.pdf",
        media_type="application/pdf"
    )
```

### Streaming Response

```python
from fastapi.responses import StreamingResponse
import io

def generate_csv():
    yield "Name,Age\n"
    yield "Alice,30\n"
    yield "Bob,25\n"

@app.get("/export")
async def export_data():
    return StreamingResponse(
        generate_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=data.csv"}
    )
```

### JSON Response with Custom Encoder

```python
from fastapi.responses import JSONResponse
from datetime import datetime

class CustomJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            default=str,  # Convert datetime to string
        ).encode("utf-8")

@app.get("/custom", response_class=CustomJSONResponse)
async def custom_response():
    return {"timestamp": datetime.now()}
```

## Templates (Jinja2)

```bash
pip install jinja2
```

```python
from fastapi.templating import Jinja2Templates
from fastapi import Request

templates = Jinja2Templates(directory="templates")

@app.get("/items/{item_id}", response_class=HTMLResponse)
async def read_item(request: Request, item_id: str):
    return templates.TemplateResponse(
        "item.html",
        {"request": request, "item_id": item_id}
    )
```

**templates/item.html:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Item {{ item_id }}</title>
</head>
<body>
    <h1>Item ID: {{ item_id }}</h1>
</body>
</html>
```

## Static Files

```python
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")
```

Access files at `/static/style.css`, `/static/script.js`, etc.

## Request Validation

### Custom Validators

```python
from pydantic import BaseModel, field_validator

class Item(BaseModel):
    name: str
    price: float

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Price must be positive")
        return v

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v
```

### Model Validators

```python
from pydantic import model_validator

class UserCreate(BaseModel):
    username: str
    password: str
    password_confirm: str

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self
```

## Custom Exception Handlers

```python
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

class CustomException(Exception):
    def __init__(self, name: str):
        self.name = name

@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=418,
        content={"message": f"Oops! {exc.name} did something wrong."}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body}
    )

@app.get("/custom/{name}")
async def read_custom(name: str):
    if name == "error":
        raise CustomException(name=name)
    return {"name": name}
```

## Request Object

Access raw request details:

```python
from fastapi import Request

@app.get("/info")
async def info(request: Request):
    return {
        "url": str(request.url),
        "method": request.method,
        "headers": dict(request.headers),
        "query_params": dict(request.query_params),
        "path_params": request.path_params,
        "client": request.client.host if request.client else None,
        "cookies": request.cookies,
    }
```

## Database Transactions

```python
from sqlmodel import Session
from fastapi import Depends, HTTPException

async def get_session_with_rollback():
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise

@app.post("/items/")
async def create_item(
    item: ItemCreate,
    session: Session = Depends(get_session_with_rollback)
):
    db_item = Item.model_validate(item)
    session.add(db_item)
    # Commit happens automatically if no exception
    return db_item
```

## Rate Limiting

```bash
pip install slowapi
```

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/limited")
@limiter.limit("5/minute")
async def limited_route(request: Request):
    return {"message": "This endpoint is rate limited"}
```

## GraphQL Integration

```bash
pip install strawberry-graphql[fastapi]
```

```python
import strawberry
from strawberry.fastapi import GraphQLRouter

@strawberry.type
class Query:
    @strawberry.field
    def hello(self, name: str = "World") -> str:
        return f"Hello {name}"

schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)

app.include_router(graphql_app, prefix="/graphql")
```

## OpenAPI Customization

```python
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Custom API",
        version="2.0.0",
        description="This is a custom OpenAPI schema",
        routes=app.routes,
    )

    openapi_schema["info"]["x-logo"] = {
        "url": "https://example.com/logo.png"
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

## Webhooks

```python
from pydantic import BaseModel

class Webhook(BaseModel):
    event: str
    data: dict

@app.post("/webhooks/")
async def receive_webhook(webhook: Webhook, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_webhook, webhook)
    return {"status": "received"}

def process_webhook(webhook: Webhook):
    # Process webhook data
    print(f"Processing webhook: {webhook.event}")
```

## Best Practices

1. **Use background tasks** for non-critical operations
2. **Add middleware judiciously** - they affect all requests
3. **WebSockets for real-time** - don't poll if WebSockets work
4. **Use lifespan events** for global setup/cleanup
5. **Custom responses** for specific media types
6. **Templates for server-side rendering** when needed
7. **Static files** served by nginx in production
8. **Validate aggressively** with Pydantic
9. **Handle exceptions** with custom handlers
10. **Rate limit** public endpoints
