---
name: sqlmodel
description: Comprehensive guide for working with SQLModel, PostgreSQL, and SQLAlchemy in FastAPI projects. Use when working with database operations in FastAPI including: (1) Defining SQLModel models and relationships, (2) Database connection and session management, (3) CRUD operations, (4) Query patterns and filtering, (5) Database migrations with Alembic, (6) Testing with SQLite, (7) Performance optimization and connection pooling, (8) Transaction management and error handling, (9) Advanced features like cascading deletes, soft deletes, and event listeners, (10) FastAPI integration patterns. Covers both basic and advanced database patterns for production-ready FastAPI applications.
---

# SQLModel for FastAPI

Comprehensive skill for building database-driven FastAPI applications with SQLModel, PostgreSQL, and SQLAlchemy.

## Quick Start

### Basic Setup

```python
# Install dependencies
pip install sqlmodel psycopg2-binary alembic pytest

# Create database models
from sqlmodel import SQLModel, Field, create_engine
from typing import Optional

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)

# Create engine and tables
engine = create_engine("postgresql://user:pass@localhost/db")
SQLModel.metadata.create_all(engine)

# Use in FastAPI
from fastapi import FastAPI, Depends
from sqlmodel import Session

app = FastAPI()

def get_session():
    with Session(engine) as session:
        yield session

@app.post("/users")
def create_user(user: User, session: Session = Depends(get_session)):
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
```

## Reference Documentation

This skill includes comprehensive reference files organized by topic. Read the relevant file based on your needs:

### Core Topics

- **[models.md](references/models.md)** - SQLModel basics, field types, constraints, table configuration, request/response models, computed fields, JSON fields, UUID keys, composite primary keys

- **[relationships.md](references/relationships.md)** - One-to-many, one-to-one, many-to-many relationships, cascade deletes, self-referential relationships, lazy vs eager loading, association object pattern

- **[sessions.md](references/sessions.md)** - Database engine setup, session management, FastAPI dependency injection, connection pooling, async sessions, multiple databases, transaction control

- **[crud.md](references/crud.md)** - Create, read, update, delete operations, bulk operations, upsert patterns, soft deletes, transaction patterns, FastAPI endpoint integration

- **[queries.md](references/queries.md)** - Where clauses, ordering, pagination, aggregations, joins, subqueries, dynamic filtering, full-text search, JSON queries, window functions, exists queries

### Advanced Topics

- **[migrations.md](references/migrations.md)** - Alembic setup and configuration, creating and applying migrations, migration operations, data migrations, branching and merging, production workflow, FastAPI integration

- **[testing.md](references/testing.md)** - Test database setup, FastAPI TestClient integration, testing CRUD operations, testing relationships, fixtures, parametrized tests, database isolation, coverage

- **[performance.md](references/performance.md)** - Connection pooling optimization, query optimization, N+1 problem solutions, indexing strategies, bulk operations, pagination best practices, caching, read replicas, batch processing

- **[integration.md](references/integration.md)** - FastAPI project structure, application lifespan, router implementation, custom dependencies, response models with relationships, error handling, middleware, background tasks, WebSocket integration

- **[advanced.md](references/advanced.md)** - Transaction management, nested transactions, cascading deletes, soft deletes, event listeners, optimistic locking, database constraints, custom field types, security best practices, monitoring and logging

## Common Workflows

### Creating a New Model

1. Define the model in your models file
2. Add relationships if needed
3. Create request/response schemas
4. Generate migration: `alembic revision --autogenerate -m "Add model"`
5. Review and apply migration: `alembic upgrade head`
6. Implement CRUD functions
7. Create API endpoints
8. Write tests

### Setting Up Database

1. Install dependencies: `pip install sqlmodel psycopg2-binary alembic`
2. Create database configuration in `database.py`
3. Define models in `models.py`
4. Initialize Alembic: `alembic init alembic`
5. Configure Alembic for SQLModel (see [migrations.md](references/migrations.md))
6. Create initial migration
7. Set up dependency injection for sessions

### Optimizing Performance

1. Add indexes on frequently queried columns (see [models.md](references/models.md))
2. Use eager loading for relationships (see [relationships.md](references/relationships.md))
3. Configure connection pooling (see [sessions.md](references/sessions.md))
4. Implement pagination (see [queries.md](references/queries.md))
5. Use bulk operations for multiple inserts/updates (see [crud.md](references/crud.md))
6. Add query caching if needed (see [performance.md](references/performance.md))

### Adding Relationships

1. Define foreign key in child model
2. Add `Relationship` field in both models
3. Use `back_populates` to link them
4. For many-to-many, create link table
5. Configure cascade behavior if needed (see [relationships.md](references/relationships.md))
6. Update migrations
7. Test relationship loading

## When to Use Each Reference

- **Starting a new project?** Read: sessions.md → models.md → integration.md
- **Need relationships?** Read: relationships.md
- **Writing queries?** Read: queries.md
- **Performance issues?** Read: performance.md → queries.md
- **Setting up testing?** Read: testing.md
- **Database migrations?** Read: migrations.md
- **Building CRUD endpoints?** Read: crud.md → integration.md
- **Advanced features?** Read: advanced.md

## Best Practices Summary

### Model Design
- Use `Optional[int]` with `default=None` for auto-increment primary keys
- Add indexes to foreign keys and frequently queried fields
- Use enums for status/category fields
- Separate table models from request/response models
- Use mixins for common fields (created_at, updated_at)

### Session Management
- Always use dependency injection in FastAPI endpoints
- Use context managers (`with Session()`) for manual sessions
- Configure connection pooling for production
- Set `pool_pre_ping=True` to handle stale connections

### Queries
- Use eager loading to avoid N+1 queries
- Add appropriate indexes before querying large datasets
- Use cursor-based pagination for large result sets
- Use `select()` for all queries instead of legacy query API

### Migrations
- Always review auto-generated migrations before applying
- Test migrations locally before production
- Make migrations reversible (implement both upgrade and downgrade)
- Use separate migrations for schema and data changes

### Testing
- Use SQLite in-memory database for tests
- Use fixtures for test data
- Override FastAPI dependencies in tests
- Test both success and failure cases

### Performance
- Index foreign keys and frequently queried columns
- Use bulk operations for multiple inserts/updates
- Configure appropriate pool sizes based on load
- Monitor slow queries and optimize them

### Security
- Never use string formatting for queries (use parameterized queries)
- Hash passwords with bcrypt or similar
- Validate all user input with Pydantic
- Use environment variables for database credentials
- Handle database errors gracefully without exposing internals

## Example Project Structure

```
app/
├── __init__.py
├── main.py              # FastAPI app with lifespan
├── database.py          # Engine and session setup
├── models.py            # SQLModel definitions
├── crud.py              # CRUD operations
├── dependencies.py      # FastAPI dependencies
├── config.py            # Settings with pydantic-settings
├── routers/
│   ├── __init__.py
│   ├── users.py
│   └── posts.py
└── tests/
    ├── __init__.py
    ├── conftest.py      # Test fixtures
    ├── test_users.py
    └── test_posts.py

alembic/
├── versions/
│   └── *.py             # Migration files
├── env.py               # Alembic configuration
└── script.py.mako

.env                     # Environment variables
alembic.ini             # Alembic config
pyproject.toml          # Dependencies
```

## Troubleshooting

### Common Issues

**Import errors with SQLModel models:**
- Ensure all models are imported in `alembic/env.py`
- Import models before calling `SQLModel.metadata.create_all()`

**N+1 query problems:**
- Use `selectinload()` or `joinedload()` for relationships
- Check query logs with `echo=True` on engine

**Connection pool exhausted:**
- Increase `pool_size` and `max_overflow`
- Ensure sessions are properly closed (use context managers)
- Check for long-running transactions

**Migration conflicts:**
- Use `alembic heads` to check for multiple heads
- Merge branches with `alembic merge`
- Resolve conflicts manually in migration files

**Slow queries:**
- Add indexes on queried columns
- Use `EXPLAIN ANALYZE` to check query plan
- Consider using read replicas for read-heavy workloads

## Additional Resources

For detailed information on specific topics, refer to the reference files in the `references/` directory. Each file contains comprehensive examples and patterns for that specific area.
