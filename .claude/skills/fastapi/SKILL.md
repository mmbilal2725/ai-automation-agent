---
name: fastapi
description: |
  Comprehensive FastAPI development skill for building production-ready Python APIs from Hello World to enterprise applications. Use this skill when the user asks about FastAPI or wants to build APIs with Python, including: (1) Creating new FastAPI projects or applications, (2) Building REST APIs with path operations, query parameters, request bodies, (3) Implementing authentication and authorization with OAuth2, JWT tokens, API keys, (4) Database integration with SQLModel, SQLAlchemy, CRUD operations, (5) Project structuring with APIRouter, dependencies, middleware, (6) Testing FastAPI applications with TestClient and pytest, (7) Deployment strategies including Docker, cloud platforms, HTTPS configuration, (8) Advanced features like WebSockets, background tasks, CORS, file uploads, (9) Debugging FastAPI issues or improving existing FastAPI code, (10) Questions about FastAPI best practices, patterns, or architecture. Triggers include phrases like "build an API", "create FastAPI app", "add authentication", "set up database", "deploy FastAPI", "test endpoints", "FastAPI tutorial", or any mention of REST API development in Python.
---

# FastAPI Development Skill

This skill provides comprehensive guidance for building FastAPI applications from simple Hello World apps to production-ready enterprise APIs.

## Quick Start Workflow

### 1. Hello World Application

For users asking to create their first FastAPI app:

```python
# Copy from: assets/hello-world.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

Run with: `fastapi dev main.py`

Access docs at: `http://127.0.0.1:8000/docs`

### 2. CRUD API Application

For users building an API with database operations:

- Use template from `assets/crud-api.py`
- Includes SQLModel setup, full CRUD operations, validation
- Covers path parameters, query parameters, request/response models

### 3. Authentication Application

For users needing authentication:

- Use template from `assets/auth-jwt.py`
- Includes JWT tokens, password hashing, OAuth2 flow
- Ready-to-use login endpoint and protected routes

## Reference Documentation

The skill includes detailed reference files for different aspects of FastAPI development. Load these as needed:

### Core Concepts
- **[references/basics.md](references/basics.md)** - Path operations, query/path parameters, request body, response models, validation, form data, file uploads, error handling
  - Use when: Starting new project, basic endpoint creation, data validation

### Dependency Injection
- **[references/dependencies.md](references/dependencies.md)** - Dependency injection system, classes as dependencies, sub-dependencies, yield dependencies, caching
  - Use when: Sharing logic, database sessions, authentication, configuration

### Security
- **[references/security.md](references/security.md)** - OAuth2, JWT tokens, password hashing, API keys, HTTP Basic Auth, CORS
  - Use when: Adding authentication, authorization, securing endpoints, user management

### Database
- **[references/databases.md](references/databases.md)** - SQLModel, CRUD operations, relationships, queries, migrations with Alembic
  - Use when: Database integration, models, CRUD endpoints, complex queries

### Project Structure
- **[references/project-structure.md](references/project-structure.md)** - APIRouter, bigger applications, file organization, API versioning
  - Use when: Structuring larger apps, organizing code, modular design

### Testing
- **[references/testing.md](references/testing.md)** - TestClient, fixtures, dependency overrides, database testing, authentication testing
  - Use when: Writing tests, test setup, mocking dependencies

### Deployment
- **[references/deployment.md](references/deployment.md)** - Docker, production servers, HTTPS, environment variables, cloud deployment
  - Use when: Deploying to production, Docker setup, HTTPS configuration

### Advanced Features
- **[references/advanced.md](references/advanced.md)** - Background tasks, middleware, WebSockets, templates, custom responses, rate limiting
  - Use when: Real-time features, background processing, custom functionality

## Common Workflows

### Workflow 1: New Project Setup

**User asks:** "Help me create a new FastAPI project"

**Steps:**
1. Determine project complexity (Hello World, CRUD API, or Full Application)
2. For simple: Use `assets/hello-world.py`
3. For CRUD: Use `assets/crud-api.py` as template
4. For auth: Include `assets/auth-jwt.py` patterns
5. Create `requirements.txt` from `assets/requirements.txt`
6. Provide `.env.example` from assets for configuration

**Installation:**
```bash
pip install "fastapi[standard]"
# Add sqlmodel for database: pip install sqlmodel
# Add auth packages: pip install "python-jose[cryptography]" "passlib[bcrypt]"
```

### Workflow 2: Adding Authentication

**User asks:** "Add authentication to my FastAPI app"

**Steps:**
1. Read `references/security.md` for OAuth2 + JWT implementation
2. Review `assets/auth-jwt.py` for complete working example
3. Implement:
   - Password hashing utilities
   - Token creation/validation
   - User authentication dependency
   - Login endpoint
   - Protected routes with `Depends(get_current_user)`
4. Configure SECRET_KEY in environment variables

### Workflow 3: Database Integration

**User asks:** "Connect my FastAPI app to a database"

**Steps:**
1. Read `references/databases.md` for SQLModel setup
2. Review `assets/crud-api.py` for complete example
3. Create models with inheritance (Base, DB, Public, Create, Update)
4. Set up engine and session dependency
5. Implement CRUD endpoints
6. For production: Set up Alembic migrations

### Workflow 4: Project Structuring

**User asks:** "How should I structure my FastAPI project?"

**Steps:**
1. Read `references/project-structure.md` for patterns
2. For small projects (<5 endpoints): Single file is fine
3. For medium projects: Use routers for different resources
4. For large projects: Implement full structure:
   ```
   app/
   ├── api/v1/endpoints/  # Route handlers
   ├── core/             # Config, security
   ├── models/           # Database models
   ├── schemas/          # Pydantic models
   ├── services/         # Business logic
   └── tests/            # Test files
   ```

### Workflow 5: Testing Setup

**User asks:** "Help me write tests for my FastAPI app"

**Steps:**
1. Read `references/testing.md` for TestClient usage
2. Install: `pip install pytest httpx`
3. Create `tests/conftest.py` with fixtures
4. Use in-memory SQLite for database tests
5. Override dependencies for authentication
6. Write tests for each endpoint (success and error cases)
7. Run: `pytest --cov=app`

### Workflow 6: Production Deployment

**User asks:** "Deploy my FastAPI app to production"

**Steps:**
1. Read `references/deployment.md` for strategies
2. Create `Dockerfile` from `assets/Dockerfile`
3. Set up `docker-compose.yml` from `assets/docker-compose.yml`
4. Configure environment variables (SECRET_KEY, DATABASE_URL)
5. Set up HTTPS with nginx reverse proxy
6. Configure Gunicorn with Uvicorn workers
7. Implement health checks
8. Set up monitoring and logging

## Progressive Implementation Guide

### Level 1: Hello World (Beginner)
- Single file application
- Basic GET endpoints
- Path and query parameters
- Run with `fastapi dev`

**Reference:** `references/basics.md` - First sections

### Level 2: CRUD API (Intermediate)
- SQLModel integration
- Full CRUD operations
- Request/response models
- Error handling
- Basic validation

**Reference:** `references/basics.md` + `references/databases.md`

### Level 3: Production API (Advanced)
- Authentication with JWT
- Project structure with routers
- Comprehensive testing
- Database migrations
- Docker deployment
- HTTPS configuration

**Reference:** All reference files

## Templates and Assets

Located in `assets/` directory:

- **hello-world.py** - Minimal FastAPI application
- **crud-api.py** - Complete CRUD API with SQLModel
- **auth-jwt.py** - Authentication with JWT tokens
- **requirements.txt** - Dependencies template
- **Dockerfile** - Production Docker setup
- **docker-compose.yml** - Multi-service deployment
- **.env.example** - Environment variables template

## Best Practices

### Code Organization
1. Use Pydantic models for validation
2. Separate database models from API schemas
3. Use dependency injection for reusable logic
4. Organize routes with APIRouter for larger apps
5. Keep business logic in service layer

### Security
1. Never commit SECRET_KEY or credentials
2. Use environment variables for configuration
3. Hash passwords with bcrypt
4. Implement HTTPS in production
5. Set appropriate CORS origins
6. Use OAuth2 scopes for fine-grained permissions

### Database
1. Use SQLModel for type safety
2. Implement separate models (Base, DB, Public, Create, Update)
3. Use Alembic for migrations in production
4. Configure connection pooling
5. Add indexes to frequently queried fields

### Testing
1. Write tests for all endpoints
2. Use in-memory database for tests
3. Override dependencies for isolation
4. Test both success and error cases
5. Aim for high coverage (>80%)

### Deployment
1. Use Gunicorn with Uvicorn workers
2. Set worker count: `(2 x num_cores) + 1`
3. Configure health checks
4. Enable compression (GZip)
5. Implement logging and monitoring
6. Use Docker for consistency
7. Configure HTTPS with Let's Encrypt

## Troubleshooting Common Issues

### Issue: "Module not found"
- Check virtual environment activation
- Verify dependencies installed: `pip install -r requirements.txt`

### Issue: "422 Validation Error"
- Check request body matches Pydantic model
- Verify field types and required fields
- Use `/docs` to see expected schema

### Issue: "401 Unauthorized"
- Verify token in Authorization header: `Bearer <token>`
- Check token expiration
- Confirm SECRET_KEY matches between creation and validation

### Issue: Database connection errors
- Verify DATABASE_URL format
- Check database is running
- For SQLite: Ensure directory exists
- For PostgreSQL/MySQL: Test connection separately

### Issue: CORS errors
- Add CORSMiddleware with appropriate origins
- Include credentials if needed
- Check allowed methods and headers

## When NOT to Use This Skill

This skill focuses on FastAPI. For other frameworks:
- Django REST Framework - use different skill/approach
- Flask - use different skill/approach
- General Python questions - standard Python knowledge applies

## Getting Help

If stuck or need more details:
1. Check appropriate reference file for topic
2. Review relevant asset template
3. Consult FastAPI official docs at https://fastapi.tiangolo.com
4. Check error messages in `/docs` endpoint for validation issues
