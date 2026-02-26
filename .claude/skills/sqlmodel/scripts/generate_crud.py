#!/usr/bin/env python3
"""
Generate CRUD boilerplate code for SQLModel models.

Usage:
    python scripts/generate_crud.py User
    python scripts/generate_crud.py Product --output app/crud/products.py
"""

import sys
import argparse
from pathlib import Path


def to_snake_case(name: str) -> str:
    """Convert CamelCase to snake_case"""
    result = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            result.append('_')
        result.append(char.lower())
    return ''.join(result)


def generate_crud_code(model_name: str) -> str:
    """Generate CRUD functions for a model"""

    snake_name = to_snake_case(model_name)
    plural_name = f"{snake_name}s"

    return f'''"""
CRUD operations for {model_name}
"""

from sqlmodel import Session, select
from typing import Optional, List
from app.models import {model_name}, {model_name}Create, {model_name}Update
from fastapi import HTTPException


def create_{snake_name}(session: Session, {snake_name}: {model_name}Create) -> {model_name}:
    """Create a new {snake_name}"""
    db_{snake_name} = {model_name}(**{snake_name}.dict())
    session.add(db_{snake_name})
    session.commit()
    session.refresh(db_{snake_name})
    return db_{snake_name}


def get_{snake_name}(session: Session, {snake_name}_id: int) -> Optional[{model_name}]:
    """Get {snake_name} by ID"""
    return session.get({model_name}, {snake_name}_id)


def get_{snake_name}_or_404(session: Session, {snake_name}_id: int) -> {model_name}:
    """Get {snake_name} by ID or raise 404"""
    {snake_name} = session.get({model_name}, {snake_name}_id)
    if not {snake_name}:
        raise HTTPException(status_code=404, detail="{model_name} not found")
    return {snake_name}


def get_{plural_name}(
    session: Session,
    skip: int = 0,
    limit: int = 100
) -> List[{model_name}]:
    """Get all {plural_name} with pagination"""
    statement = select({model_name}).offset(skip).limit(limit)
    return session.exec(statement).all()


def update_{snake_name}(
    session: Session,
    {snake_name}_id: int,
    {snake_name}_update: {model_name}Update
) -> {model_name}:
    """Update {snake_name}"""
    db_{snake_name} = get_{snake_name}_or_404(session, {snake_name}_id)

    # Update only provided fields
    update_data = {snake_name}_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_{snake_name}, key, value)

    session.add(db_{snake_name})
    session.commit()
    session.refresh(db_{snake_name})
    return db_{snake_name}


def delete_{snake_name}(session: Session, {snake_name}_id: int) -> None:
    """Delete {snake_name}"""
    db_{snake_name} = get_{snake_name}_or_404(session, {snake_name}_id)
    session.delete(db_{snake_name})
    session.commit()
'''


def generate_router_code(model_name: str) -> str:
    """Generate FastAPI router for a model"""

    snake_name = to_snake_case(model_name)
    plural_name = f"{snake_name}s"

    return f'''"""
API routes for {model_name}
"""

from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from typing import List
from app.database import get_session
from app.models import {model_name}Create, {model_name}Update, {model_name}Read
from app.crud import {plural_name} as crud


router = APIRouter(
    prefix="/{plural_name}",
    tags=["{plural_name}"]
)


@router.post("", response_model={model_name}Read, status_code=status.HTTP_201_CREATED)
def create_{snake_name}(
    {snake_name}: {model_name}Create,
    session: Session = Depends(get_session)
):
    """Create a new {snake_name}"""
    return crud.create_{snake_name}(session, {snake_name})


@router.get("/{{{{{}}_id}}}}", response_model={model_name}Read)
def read_{snake_name}(
    {snake_name}_id: int,
    session: Session = Depends(get_session)
):
    """Get {snake_name} by ID"""
    return crud.get_{snake_name}_or_404(session, {snake_name}_id)


@router.get("", response_model=List[{model_name}Read])
def read_{plural_name}(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """Get all {plural_name}"""
    return crud.get_{plural_name}(session, skip=skip, limit=limit)


@router.put("/{{{{{}}_id}}}}", response_model={model_name}Read)
def update_{snake_name}(
    {snake_name}_id: int,
    {snake_name}: {model_name}Update,
    session: Session = Depends(get_session)
):
    """Update {snake_name}"""
    return crud.update_{snake_name}(session, {snake_name}_id, {snake_name})


@router.delete("/{{{{{}}_id}}}}", status_code=status.HTTP_204_NO_CONTENT)
def delete_{snake_name}(
    {snake_name}_id: int,
    session: Session = Depends(get_session)
):
    """Delete {snake_name}"""
    crud.delete_{snake_name}(session, {snake_name}_id)
    return None
'''


def main():
    parser = argparse.ArgumentParser(
        description="Generate CRUD boilerplate for SQLModel models"
    )
    parser.add_argument(
        "model",
        type=str,
        help="Model name (e.g., User, Product)"
    )
    parser.add_argument(
        "--crud-output",
        type=str,
        help="Output file for CRUD functions",
        default=None
    )
    parser.add_argument(
        "--router-output",
        type=str,
        help="Output file for router",
        default=None
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print to stdout instead of writing to files"
    )

    args = parser.parse_args()

    model_name = args.model
    snake_name = to_snake_case(model_name)

    # Generate code
    crud_code = generate_crud_code(model_name)
    router_code = generate_router_code(model_name)

    if args.print_only:
        print("=" * 80)
        print(f"CRUD Functions for {model_name}")
        print("=" * 80)
        print(crud_code)
        print("\n" + "=" * 80)
        print(f"Router for {model_name}")
        print("=" * 80)
        print(router_code)
    else:
        # Determine output paths
        crud_output = args.crud_output or f"app/crud/{snake_name}s.py"
        router_output = args.router_output or f"app/routers/{snake_name}s.py"

        # Create directories if needed
        Path(crud_output).parent.mkdir(parents=True, exist_ok=True)
        Path(router_output).parent.mkdir(parents=True, exist_ok=True)

        # Write files
        with open(crud_output, "w") as f:
            f.write(crud_code)
        print(f"✅ Created CRUD functions: {crud_output}")

        with open(router_output, "w") as f:
            f.write(router_code)
        print(f"✅ Created router: {router_output}")

        print(f"\\nNext steps:")
        print(f"1. Define {model_name}Create, {model_name}Update, {model_name}Read in app/models.py")
        print(f"2. Import router in app/main.py:")
        print(f"   from app.routers import {snake_name}s")
        print(f"   app.include_router({snake_name}s.router)")


if __name__ == "__main__":
    main()
