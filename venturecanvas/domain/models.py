"""Model layer of MVC — SQLModel entity classes for VentureCanvas.

The domain is intentionally small (three entities) so it maps one-to-one
onto the twelve features listed in Plan.md §3::

    User ──< Project
       \\      |
        \\     v
         >── CollectionItem  (unique per (user, project))

Every user-facing column carries explicit :func:`sqlmodel.Field`
validation (``min_length``/``max_length``, ``unique``, ``index``) per
Plan.md §7 so that validation errors surface at object construction
time — there is no second validation pass living in services or
controllers.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


class Category(str, Enum):
    """Closed set of project categories used for browsing and filtering.

    The five values match the category chips on the home page. Any new
    category must be added here first — pydantic validation will reject
    anything else when a :class:`Project` is constructed.
    """

    IOT = "IoT"
    AI = "AI"
    WEB = "Web"
    MOBILE = "Mobile"
    HARDWARE = "Hardware"


class User(SQLModel, table=True):
    """A registered person who can own projects and curate a collection.

    ``password_hash`` stores the full PBKDF2 derivation produced by
    :class:`venturecanvas.services.auth_service.AuthService` in a single
    ``"{iterations}${salt_hex}${hash_hex}"`` string; the model never
    touches plaintext passwords.
    """

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, min_length=3, max_length=40)
    email: str = Field(index=True, unique=True, max_length=120)
    password_hash: str = Field(max_length=256)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    projects: list["Project"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    collection_items: list["CollectionItem"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Project(SQLModel, table=True):
    """An innovation project posted by a user.

    The four ``required_*`` fields are comma-separated free text. The
    collection summary splits and unions them across every saved project,
    so a curator can see at a glance what skills / tools / APIs / hardware
    they'd need to execute their whole collection.
    """

    __tablename__ = "projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=1, max_length=2000)
    category: Category = Field(index=True)
    required_skills: str = Field(default="", max_length=300)
    required_tools: str = Field(default="", max_length=300)
    required_apis: str = Field(default="", max_length=300)
    required_hardware: str = Field(default="", max_length=300)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    owner: "User" = Relationship(back_populates="projects")
    collection_items: list["CollectionItem"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class CollectionItem(SQLModel, table=True):
    """A project saved to a user's personal collection.

    The ``UniqueConstraint`` prevents a project from being added to the
    same collection twice; the collection service catches the resulting
    :class:`sqlalchemy.exc.IntegrityError` and raises its own typed
    error so the UI can show a friendly message.
    """

    __tablename__ = "collection_items"
    __table_args__ = (
        UniqueConstraint("user_id", "project_id", name="uq_collection_user_project"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    added_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    user: "User" = Relationship(back_populates="collection_items")
    project: "Project" = Relationship(back_populates="collection_items")
