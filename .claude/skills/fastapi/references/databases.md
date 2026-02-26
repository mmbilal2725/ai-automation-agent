# FastAPI with SQL Databases

## Overview

FastAPI works seamlessly with SQL databases using **SQLModel**, which combines SQLAlchemy and Pydantic. SQLModel provides type safety, validation, and automatic OpenAPI documentation.

## Installation

```bash
pip install sqlmodel
```

SQLModel supports all SQLAlchemy-compatible databases:
- PostgreSQL
- MySQL
- SQLite
- Oracle
- Microsoft SQL Server

## Basic Setup

### 1. Define Models

```python
from sqlmodel import Field, SQLModel

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    secret_name: str
    age: int | None = Field(default=None, index=True)
```

**Key features:**
- `table=True`: Marks this as a database table model
- `Field(primary_key=True)`: Primary key column
- `Field(index=True)`: Creates database index
- Type hints define column types

### 2. Create Engine

```python
from sqlmodel import create_engine

# SQLite
sqlite_url = "sqlite:///database.db"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

# PostgreSQL
postgres_url = "postgresql://user:password@localhost/dbname"
engine = create_engine(postgres_url)

# MySQL
mysql_url = "mysql://user:password@localhost/dbname"
engine = create_engine(mysql_url)
```

**SQLite note:** `check_same_thread=False` allows FastAPI to use SQLite across threads.

### 3. Create Tables

```python
from sqlmodel import SQLModel

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Call on app startup
from fastapi import FastAPI

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
```

### 4. Session Dependency

```python
from typing import Annotated
from fastapi import Depends
from sqlmodel import Session

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
```

## Model Patterns

### Single Model (Simple)

```python
from sqlmodel import Field, SQLModel

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: int | None = None
```

**Issue:** Exposes all fields (including `secret_name`) in API responses.

### Multiple Models with Inheritance (Recommended)

```python
# Base model with shared fields
class HeroBase(SQLModel):
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)

# Database table model
class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    secret_name: str

# Public response model (excludes sensitive fields)
class HeroPublic(HeroBase):
    id: int

# Creation model (no auto-generated fields)
class HeroCreate(HeroBase):
    secret_name: str

# Update model (all fields optional)
class HeroUpdate(SQLModel):
    name: str | None = None
    age: int | None = None
    secret_name: str | None = None
```

**Benefits:**
- Separate input/output models
- Security (don't expose `secret_name`)
- Flexibility (different fields for create/update/read)

## CRUD Operations

### Create

```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/heroes/", response_model=HeroPublic)
def create_hero(hero: HeroCreate, session: SessionDep):
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero
```

**Flow:**
1. `Hero.model_validate(hero)`: Convert `HeroCreate` to `Hero`
2. `session.add()`: Add to session
3. `session.commit()`: Save to database
4. `session.refresh()`: Get auto-generated fields (like `id`)

### Read All

```python
from sqlmodel import select

@app.get("/heroes/", response_model=list[HeroPublic])
def read_heroes(
    session: SessionDep,
    offset: int = 0,
    limit: int = Query(default=100, le=100),
):
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes
```

**Features:**
- Pagination with `offset` and `limit`
- `limit` capped at 100 for performance

### Read One

```python
from fastapi import HTTPException

@app.get("/heroes/{hero_id}", response_model=HeroPublic)
def read_hero(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero
```

**Alternative with select:**
```python
@app.get("/heroes/{hero_id}", response_model=HeroPublic)
def read_hero(hero_id: int, session: SessionDep):
    hero = session.exec(select(Hero).where(Hero.id == hero_id)).first()
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero
```

### Update

```python
@app.patch("/heroes/{hero_id}", response_model=HeroPublic)
def update_hero(hero_id: int, hero: HeroUpdate, session: SessionDep):
    db_hero = session.get(Hero, hero_id)
    if not db_hero:
        raise HTTPException(status_code=404, detail="Hero not found")

    hero_data = hero.model_dump(exclude_unset=True)
    db_hero.sqlmodel_update(hero_data)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero
```

**Key points:**
- `exclude_unset=True`: Only update fields that were actually provided
- `sqlmodel_update()`: Update model attributes
- Use `PATCH` for partial updates, `PUT` for full replacements

### Delete

```python
@app.delete("/heroes/{hero_id}")
def delete_hero(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")

    session.delete(hero)
    session.commit()
    return {"ok": True}
```

## Relationships

### One-to-Many

```python
from sqlmodel import Field, Relationship, SQLModel

class Team(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    headquarters: str

    heroes: list["Hero"] = Relationship(back_populates="team")

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    secret_name: str
    age: int | None = None

    team_id: int | None = Field(default=None, foreign_key="team.id")
    team: Team | None = Relationship(back_populates="heroes")
```

**Usage:**
```python
# Create team with heroes
team = session.get(Team, team_id)
heroes = team.heroes  # Automatically loaded

# Create hero with team
hero = Hero(name="Spider-Boy", secret_name="Pedro", team_id=1)
```

### Many-to-Many

```python
from sqlmodel import Field, Relationship, SQLModel

class HeroTeamLink(SQLModel, table=True):
    team_id: int | None = Field(default=None, foreign_key="team.id", primary_key=True)
    hero_id: int | None = Field(default=None, foreign_key="hero.id", primary_key=True)

class Team(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)

    heroes: list["Hero"] = Relationship(back_populates="teams", link_model=HeroTeamLink)

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)

    teams: list[Team] = Relationship(back_populates="heroes", link_model=HeroTeamLink)
```

## Advanced Queries

### Filtering

```python
from sqlmodel import select

# Simple filter
heroes = session.exec(select(Hero).where(Hero.age >= 35)).all()

# Multiple conditions (AND)
heroes = session.exec(
    select(Hero)
    .where(Hero.age >= 35)
    .where(Hero.age < 40)
).all()

# OR conditions
from sqlmodel import or_

heroes = session.exec(
    select(Hero).where(
        or_(Hero.age <= 35, Hero.age > 90)
    )
).all()
```

### Ordering

```python
# Ascending
heroes = session.exec(select(Hero).order_by(Hero.age)).all()

# Descending
from sqlmodel import desc

heroes = session.exec(select(Hero).order_by(desc(Hero.age))).all()
```

### Joins

```python
# Explicit join
statement = select(Hero, Team).join(Team).where(Team.name == "Preventers")
results = session.exec(statement)
for hero, team in results:
    print(f"{hero.name} is in {team.name}")

# Automatic relationship loading
hero = session.get(Hero, hero_id)
team = hero.team  # Loads team automatically
```

### Aggregations

```python
from sqlmodel import func, select

# Count
count = session.exec(select(func.count()).select_from(Hero)).one()

# Average
avg_age = session.exec(select(func.avg(Hero.age))).one()

# Group by
statement = select(Hero.team_id, func.count(Hero.id)).group_by(Hero.team_id)
results = session.exec(statement).all()
```

## Database Migrations (Alembic)

For production, use Alembic for schema versioning:

### Installation

```bash
pip install alembic
```

### Initialize

```bash
alembic init alembic
```

### Configure

Edit `alembic/env.py`:
```python
from sqlmodel import SQLModel
from yourapp.models import Hero  # Import your models

target_metadata = SQLModel.metadata
```

### Create Migration

```bash
alembic revision --autogenerate -m "Add heroes table"
```

### Apply Migration

```bash
alembic upgrade head
```

### Rollback

```bash
alembic downgrade -1
```

## Testing with In-Memory Database

```python
from sqlmodel import create_engine, Session, SQLModel

def test_create_hero():
    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        hero = Hero(name="Test Hero", secret_name="Test")
        session.add(hero)
        session.commit()

        assert hero.id is not None
```

## Best Practices

1. **Use type aliases** for session dependency
2. **Separate models** for input/output/database
3. **Use migrations** (Alembic) for production schema changes
4. **Close sessions properly** with context managers or yield dependencies
5. **Index frequently queried fields** with `Field(index=True)`
6. **Use pagination** for list endpoints
7. **Validate relationships** exist before creating foreign keys
8. **Handle exceptions** (database errors, constraint violations)
9. **Use connection pooling** for production (SQLAlchemy default)
10. **Consider read replicas** for high-traffic applications

## Connection String Examples

```python
# SQLite (file-based)
"sqlite:///./database.db"

# SQLite (in-memory)
"sqlite:///:memory:"

# PostgreSQL
"postgresql://user:password@localhost/dbname"
"postgresql+asyncpg://user:password@localhost/dbname"  # async

# MySQL
"mysql://user:password@localhost/dbname"
"mysql+pymysql://user:password@localhost/dbname"

# SQL Server
"mssql+pyodbc://user:password@localhost/dbname?driver=ODBC+Driver+17+for+SQL+Server"
```

## Async Database Support

```python
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

async_engine = create_async_engine("postgresql+asyncpg://user:password@localhost/dbname")

async def get_session():
    async with AsyncSession(async_engine) as session:
        yield session

@app.get("/heroes/")
async def read_heroes(session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(Hero))
    heroes = result.all()
    return heroes
```
