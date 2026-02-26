#!/usr/bin/env python3
"""
Database initialization script for SQLModel projects.

Usage:
    python scripts/init_db.py

This script creates all database tables based on SQLModel definitions.
"""

import os
import sys
from sqlmodel import SQLModel, create_engine

def init_db(database_url: str = None):
    """Initialize database tables"""

    # Get database URL from environment or parameter
    if database_url is None:
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://user:password@localhost:5432/dbname"
        )

    print(f"Connecting to database...")
    print(f"URL: {database_url.split('@')[1] if '@' in database_url else 'SQLite'}")

    try:
        # Create engine
        engine = create_engine(database_url, echo=False)

        # Create all tables
        print("Creating database tables...")
        SQLModel.metadata.create_all(engine)

        print("✅ Database tables created successfully!")

    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)


def drop_db(database_url: str = None):
    """Drop all database tables"""

    if database_url is None:
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://user:password@localhost:5432/dbname"
        )

    print(f"⚠️  WARNING: This will drop all tables!")
    confirm = input("Type 'yes' to confirm: ")

    if confirm.lower() != 'yes':
        print("Aborted.")
        return

    try:
        engine = create_engine(database_url, echo=False)

        print("Dropping all tables...")
        SQLModel.metadata.drop_all(engine)

        print("✅ All tables dropped successfully!")

    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database initialization")
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop all tables instead of creating them"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="Database URL (overrides DATABASE_URL env var)"
    )

    args = parser.parse_args()

    if args.drop:
        drop_db(args.url)
    else:
        init_db(args.url)
