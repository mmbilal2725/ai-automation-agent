# SQLModel Relationships

## One-to-Many Relationship

```python
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

# Parent model
class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Relationship to Hero (one team has many heroes)
    heroes: List["Hero"] = Relationship(back_populates="team")

# Child model
class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")

    # Relationship to Team (many heroes belong to one team)
    team: Optional[Team] = Relationship(back_populates="heroes")
```

## One-to-One Relationship

```python
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str

    # One-to-one: uselist=False
    profile: Optional["UserProfile"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"uselist": False}
    )

class UserProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

    user: Optional[User] = Relationship(back_populates="profile")
```

## Many-to-Many Relationship

```python
# Link table
class StudentCourseLink(SQLModel, table=True):
    student_id: int = Field(foreign_key="student.id", primary_key=True)
    course_id: int = Field(foreign_key="course.id", primary_key=True)

    # Optional: extra fields in the link table
    enrolled_at: datetime = Field(default_factory=datetime.utcnow)
    grade: Optional[float] = None

class Student(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    # Many-to-many with link model
    courses: List["Course"] = Relationship(
        back_populates="students",
        link_model=StudentCourseLink
    )

class Course(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str

    students: List[Student] = Relationship(
        back_populates="courses",
        link_model=StudentCourseLink
    )
```

## Cascade Delete

```python
from sqlalchemy import ForeignKey, Column, Integer
from sqlalchemy.orm import relationship as sa_relationship

class Author(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    # Cascade delete: when author is deleted, all books are deleted
    books: List["Book"] = Relationship(
        back_populates="author",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class Book(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    author_id: int = Field(foreign_key="author.id")

    author: Author = Relationship(back_populates="books")
```

## Self-Referential Relationship

```python
class Employee(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    manager_id: Optional[int] = Field(default=None, foreign_key="employee.id")

    # Self-referential: employee can have a manager (another employee)
    manager: Optional["Employee"] = Relationship(
        back_populates="subordinates",
        sa_relationship_kwargs={
            "remote_side": "Employee.id"  # Specify the remote side
        }
    )

    # One manager has many subordinates
    subordinates: List["Employee"] = Relationship(back_populates="manager")
```

## Lazy Loading vs Eager Loading

```python
from sqlalchemy.orm import selectinload

# Default: lazy loading (queries relationships only when accessed)
class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    comments: List["Comment"] = Relationship(back_populates="post")

# Eager loading in query
from sqlmodel import select, Session

with Session(engine) as session:
    # Lazy loading (default) - additional query when accessing comments
    post = session.get(Post, 1)
    comments = post.comments  # Triggers additional query

    # Eager loading - load comments in same query
    statement = select(Post).options(selectinload(Post.comments))
    post = session.exec(statement).first()
    comments = post.comments  # No additional query
```

## Multiple Relationships to Same Table

```python
class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str

    # Multiple FKs to User table
    sender_id: int = Field(foreign_key="user.id")
    recipient_id: int = Field(foreign_key="user.id")

    # Named relationships with foreign_keys parameter
    sender: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Message.sender_id]"}
    )

    recipient: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Message.recipient_id]"}
    )

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str

    # Corresponding back-references
    sent_messages: List[Message] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Message.sender_id]"}
    )

    received_messages: List[Message] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Message.recipient_id]"}
    )
```

## Relationship with Filter

```python
from datetime import datetime, timedelta

class Blog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str

    # All posts
    posts: List["Post"] = Relationship(back_populates="blog")

    # Only recent posts (last 30 days)
    recent_posts: List["Post"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "and_(Post.blog_id==Blog.id, Post.created_at>=datetime.utcnow()-timedelta(days=30))",
            "viewonly": True
        }
    )

class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    blog_id: int = Field(foreign_key="blog.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    blog: Blog = Relationship(back_populates="posts")
```

## Association Object Pattern

```python
# When the link table needs methods/properties
class OrderItem(SQLModel, table=True):
    order_id: int = Field(foreign_key="order.id", primary_key=True)
    product_id: int = Field(foreign_key="product.id", primary_key=True)
    quantity: int = Field(ge=1)
    unit_price: Decimal

    # Relationships to both sides
    order: "Order" = Relationship(back_populates="items")
    product: "Product" = Relationship(back_populates="order_items")

    @property
    def total_price(self) -> Decimal:
        return self.quantity * self.unit_price

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_name: str

    # Direct access to association objects
    items: List[OrderItem] = Relationship(back_populates="order")

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: Decimal

    order_items: List[OrderItem] = Relationship(back_populates="product")
```
