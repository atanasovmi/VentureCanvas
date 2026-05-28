"""Model layer of MVC — SQLModel entity classes for VentureCanvas.

The domain is intentionally small (three entities) so it maps one-to-one
onto the twelve features listed in Plan.md §3::

    User ──< Project
       \\      |
        \\     v
         >── CollectionItem  (unique per (user, project))

Every user-facing column declares its constraints with
:func:`sqlmodel.Field` (``min_length``/``max_length``, ``unique``,
``index``) per Plan.md §7. Those declarations are the single declarative
source of truth and shape the generated SQL schema, but they are *not*
the runtime enforcement point: these are ``table=True`` models, so
SQLModel disables pydantic validation at construction, and SQLite ignores
``VARCHAR`` length. The database therefore enforces only the structural
constraints — ``unique=True`` on username/email and the
:class:`CollectionItem` ``UniqueConstraint``. Length and format rules are
enforced in the service layer
(:class:`~venturecanvas.services.auth_service.AuthService`,
:class:`~venturecanvas.services.project_service.ProjectService`), which
re-checks the same bounds before persisting.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


class Category(str, Enum):
    """Closed set of project categories used for browsing and filtering.

    The five values match the category chips on the home page; any new
    category must be added here first. Because :class:`Project` is a
    ``table=True`` model it does *not* reject an out-of-set value at
    construction, so
    :class:`~venturecanvas.services.project_service.ProjectService` coerces
    incoming categories through ``Category(value)`` to keep callers inside
    this set.
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

    id: Optional[int] = Field(default=None, primary_key=True)       # auto-assigned PK
    username: str = Field(index=True, unique=True, min_length=3, max_length=40)  # login handle; unique
    email: str = Field(index=True, unique=True, max_length=120)     # login id; stored lowercased
    password_hash: str = Field(max_length=256)                      # PBKDF2 string — never plaintext
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),         # stamped once, in UTC
    )

    # cascade="all, delete-orphan": deleting a user removes their projects and
    # collection rows too, so no orphaned children survive.
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

    id: Optional[int] = Field(default=None, primary_key=True)       # auto-assigned PK
    owner_id: int = Field(foreign_key="users.id", index=True)       # FK → the author; indexed for "my projects"
    title: str = Field(min_length=2, max_length=200)                # bounds enforced in ProjectService
    description: str = Field(min_length=1, max_length=2000)         # required; bounds enforced in service
    category: Category = Field(index=True)                          # one of the five chips; indexed for filtering
    # The four requirement lists are free-text, comma-separated. The collection
    # summary splits and unions them across saved projects (see CollectionService).
    required_skills: str = Field(default="", max_length=300)
    required_tools: str = Field(default="", max_length=300)
    required_apis: str = Field(default="", max_length=300)
    required_hardware: str = Field(default="", max_length=300)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),         # set once at creation
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),         # refreshed by ProjectService.update
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
    # The (user_id, project_id) pair is unique → the same project can't be
    # saved to one collection twice. This is the one DB-enforced business rule.
    __table_args__ = (
        UniqueConstraint("user_id", "project_id", name="uq_collection_user_project"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)       # auto-assigned PK
    user_id: int = Field(foreign_key="users.id", index=True)        # FK → the curator
    project_id: int = Field(foreign_key="projects.id", index=True)  # FK → the saved project
    added_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),         # newest-first ordering key
    )

    user: "User" = Relationship(back_populates="collection_items")
    project: "Project" = Relationship(back_populates="collection_items")
