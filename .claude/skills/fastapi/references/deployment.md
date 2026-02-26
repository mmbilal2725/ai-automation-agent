# FastAPI Deployment

## Overview

Deploying FastAPI applications involves running a production-grade server, configuring security (HTTPS), managing workers for scalability, and containerization. This guide covers production deployment strategies.

## Production Servers

### Uvicorn (ASGI Server)

FastAPI runs on Uvicorn, an ASGI server. For production, use Uvicorn with Gunicorn for process management.

#### Basic Uvicorn

```bash
# Development
fastapi dev main.py

# Production (single worker)
fastapi run main.py

# Or with uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Uvicorn with Workers

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Workers formula:** `(2 x num_cores) + 1`

### Gunicorn with Uvicorn Workers

```bash
pip install gunicorn
```

```bash
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
```

**Configuration file (gunicorn.conf.py):**
```python
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "fastapi-app"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None
```

**Run with config:**
```bash
gunicorn -c gunicorn.conf.py app.main:app
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /code

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy application
COPY ./app /code/app

# Run the application
CMD ["fastapi", "run", "app/main.py", "--port", "80"]
```

### Optimized Multi-Stage Dockerfile

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /code

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /code

# Copy dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy application
COPY ./app /code/app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /code
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:80/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--workers", "4"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:80"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/dbname
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=dbname
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
```

### Build and Run

```bash
# Build
docker build -t fastapi-app .

# Run
docker run -d -p 8000:80 --name fastapi-container fastapi-app

# With docker-compose
docker-compose up -d
docker-compose logs -f
docker-compose down
```

## Environment Variables

### .env File

```
# .env
SECRET_KEY=your-super-secret-key
DATABASE_URL=postgresql://user:password@localhost/dbname
ALLOWED_HOSTS=example.com,www.example.com
CORS_ORIGINS=https://example.com,https://app.example.com
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Settings Management

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "FastAPI App"
    secret_key: str
    database_url: str
    allowed_hosts: list[str] = []
    cors_origins: list[str] = []
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
```

## HTTPS Configuration

### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/fastapi-app

upstream fastapi_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name example.com www.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com www.example.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files (if needed)
    location /static/ {
        alias /var/www/fastapi-app/static/;
    }
}
```

### Let's Encrypt SSL

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d example.com -d www.example.com

# Auto-renewal
sudo certbot renew --dry-run
```

## Cloud Deployment

### AWS (Elastic Beanstalk)

**Procfile:**
```
web: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Deploy:**
```bash
eb init -p python-3.11 fastapi-app
eb create fastapi-env
eb deploy
```

### Google Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/fastapi-app
gcloud run deploy --image gcr.io/PROJECT_ID/fastapi-app --platform managed
```

### Heroku

**Procfile:**
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Deploy:**
```bash
heroku create fastapi-app
git push heroku main
```

### Railway

**railway.toml:**
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

## Monitoring and Logging

### Structured Logging

```python
import logging
from pythonjsonlogger import jsonlogger

# Configure logger
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Use in app
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    logger.info("Reading item", extra={"item_id": item_id})
    return {"item_id": item_id}
```

### Prometheus Metrics

```bash
pip install prometheus-fastapi-instrumentator
```

```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

Instrumentator().instrument(app).expose(app)
```

Access metrics at `/metrics`.

### Sentry Error Tracking

```bash
pip install sentry-sdk[fastapi]
```

```python
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0,
)

app = FastAPI()
```

## Performance Optimization

### Caching

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

@app.get("/items/")
@cache(expire=60)
async def read_items():
    return {"items": []}
```

### Database Connection Pooling

```python
from sqlmodel import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

### Compression

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

## Health Checks

```python
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/ready")
async def readiness_check(session: SessionDep):
    try:
        # Check database connection
        session.exec(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Not ready")
```

## Deployment Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Use environment variables for secrets
- [ ] Configure HTTPS/TLS
- [ ] Set up database connection pooling
- [ ] Configure CORS properly
- [ ] Enable compression
- [ ] Set up logging and monitoring
- [ ] Configure health checks
- [ ] Use multiple workers
- [ ] Set resource limits (memory, CPU)
- [ ] Configure backups
- [ ] Set up CI/CD pipeline
- [ ] Enable rate limiting
- [ ] Configure firewall rules
- [ ] Set up automated testing
- [ ] Document deployment process

## Best Practices

1. **Use environment-specific configs** - dev, staging, production
2. **Run migrations before deployment** - automate with CI/CD
3. **Zero-downtime deployments** - blue/green or rolling updates
4. **Monitor application health** - uptime, response times, errors
5. **Set up alerts** - for errors, high latency, downtime
6. **Regular backups** - database and critical files
7. **Security updates** - keep dependencies updated
8. **Load testing** - before production deployment
9. **Rollback plan** - test and document rollback procedure
10. **Documentation** - deployment process, architecture, runbooks
