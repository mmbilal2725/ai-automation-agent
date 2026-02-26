# Database Migrations with Alembic

## Alembic Setup

```bash
# Install Alembic
pip install alembic

# Initialize Alembic
alembic init alembic
```

## Configure Alembic for SQLModel

Edit `alembic/env.py`:

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from sqlmodel import SQLModel

# Import all models to ensure metadata is complete
from app.models import User, Post, Comment  # Import all your models

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata from SQLModel
target_metadata = SQLModel.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

Edit `alembic.ini`:

```ini
# Set your database URL
sqlalchemy.url = postgresql://user:password@localhost:5432/dbname

# Or use environment variable
# sqlalchemy.url = driver://user:pass@localhost/dbname
```

## Using Environment Variables

Edit `alembic/env.py` to read from environment:

```python
import os
from dotenv import load_dotenv

load_dotenv()  # Load .env file

# Override database URL from environment
config.set_main_option(
    "sqlalchemy.url",
    os.getenv("DATABASE_URL", "postgresql://localhost/dbname")
)
```

## Creating Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add user table"

# Create empty migration (for manual edits)
alembic revision -m "Add custom constraint"

# Check current version
alembic current

# Show migration history
alembic history
```

## Applying Migrations

```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade by specific number of revisions
alembic upgrade +1

# Upgrade to specific revision
alembic upgrade abc123

# Downgrade by one revision
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade abc123

# Show SQL without executing
alembic upgrade head --sql
```

## Migration File Structure

Example migration file:

```python
"""Add user table

Revision ID: abc123def456
Revises:
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers
revision = 'abc123def456'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Apply migration"""
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index('ix_user_username', 'user', ['username'])

def downgrade() -> None:
    """Revert migration"""
    op.drop_index('ix_user_username', table_name='user')
    op.drop_table('user')
```

## Common Migration Operations

```python
# Add column
op.add_column('user', sa.Column('phone', sa.String(20), nullable=True))

# Drop column
op.drop_column('user', 'phone')

# Rename column
op.alter_column('user', 'username', new_column_name='user_name')

# Change column type
op.alter_column('user', 'age',
    type_=sa.Integer(),
    existing_type=sa.String()
)

# Add NOT NULL constraint
op.alter_column('user', 'email',
    nullable=False,
    existing_type=sa.String()
)

# Create index
op.create_index('ix_user_email', 'user', ['email'])

# Drop index
op.drop_index('ix_user_email', table_name='user')

# Add unique constraint
op.create_unique_constraint('uq_user_email', 'user', ['email'])

# Drop unique constraint
op.drop_constraint('uq_user_email', 'user', type_='unique')

# Add foreign key
op.create_foreign_key(
    'fk_post_user_id',
    'post', 'user',
    ['user_id'], ['id'],
    ondelete='CASCADE'
)

# Drop foreign key
op.drop_constraint('fk_post_user_id', 'post', type_='foreignkey')
```

## Data Migrations

```python
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    """Populate default data"""
    # Get connection
    connection = op.get_bind()

    # Insert data
    connection.execute(
        sa.text("""
            INSERT INTO role (name, description)
            VALUES
                ('admin', 'Administrator'),
                ('user', 'Regular user'),
                ('moderator', 'Content moderator')
        """)
    )

    # Update existing data
    connection.execute(
        sa.text("""
            UPDATE user
            SET role = 'user'
            WHERE role IS NULL
        """)
    )

def downgrade() -> None:
    """Revert data changes"""
    connection = op.get_bind()
    connection.execute(sa.text("DELETE FROM role"))
```

## Branching and Merging

```bash
# Create branch
alembic revision -m "Feature branch" --branch-label feature

# Merge branches
alembic merge -m "Merge feature" head1 head2

# Resolve conflicts manually in migration files
```

## Testing Migrations

```python
# Test upgrade and downgrade
def test_migration():
    # Run upgrade
    alembic upgrade head

    # Verify changes
    # ... test code ...

    # Run downgrade
    alembic downgrade -1

    # Verify rollback
    # ... test code ...
```

## Best Practices

```python
# ✅ GOOD: Descriptive migration message
alembic revision --autogenerate -m "Add user email verification fields"

# ❌ BAD: Vague message
alembic revision --autogenerate -m "Update user"

# ✅ GOOD: Review auto-generated migrations
# Always check and edit auto-generated migrations before applying

# ✅ GOOD: Test migrations locally first
alembic upgrade head  # Test on local database
alembic downgrade -1  # Test rollback
alembic upgrade head  # Apply again

# ✅ GOOD: Separate data and schema migrations
# Use separate migrations for schema changes and data population

# ✅ GOOD: Make migrations reversible
# Always implement both upgrade() and downgrade()

# ❌ BAD: Irreversible downgrade
def downgrade() -> None:
    pass  # Don't leave empty!
```

## Production Workflow

```bash
# Development
1. Make model changes
2. alembic revision --autogenerate -m "Description"
3. Review and edit migration file
4. alembic upgrade head (test locally)
5. Commit migration file to version control

# Staging
1. Pull latest code
2. alembic upgrade head
3. Test thoroughly

# Production
1. Backup database
2. alembic current (check current version)
3. alembic upgrade head --sql > migration.sql (generate SQL)
4. Review SQL
5. alembic upgrade head (apply migration)
6. Verify changes
7. Monitor application
```

## Integration with FastAPI

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from alembic.config import Config
from alembic import command

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run migrations on startup"""
    # Run migrations
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    yield

    # Cleanup on shutdown
    pass

app = FastAPI(lifespan=lifespan)
```

## Handling Multiple Databases

```ini
# alembic.ini
[alembic:primary]
sqlalchemy.url = postgresql://localhost/primary_db

[alembic:analytics]
sqlalchemy.url = postgresql://localhost/analytics_db
```

```bash
# Specify environment
alembic -n primary upgrade head
alembic -n analytics upgrade head
```
