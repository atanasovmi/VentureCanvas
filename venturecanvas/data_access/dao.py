"""Repository / DAO layer.

Every DAO subclasses :class:`BaseDAO` and operates on a
:class:`sqlmodel.Session` passed in by the service caller. The service
opens that session with
:meth:`venturecanvas.data_access.db.Database.session_scope`, so the
whole business operation is a single transactional unit — services
never see raw engines or commits.
"""

from __future__ import annotations

from typing import Generic, List, Optional, Type, TypeVar

from sqlmodel import Session, SQLModel, select

from ..domain.models import Category, CollectionItem, Project, User

ModelT = TypeVar("ModelT", bound=SQLModel)


class BaseDAO(Generic[ModelT]):
    """Generic repository over a SQLModel entity.

    Subclasses must set the class attribute :attr:`model` to the
    concrete :class:`sqlmodel.SQLModel` class they manage. The generic
    parameter exists only for typing.
    """

    model: Type[ModelT]

    def add(self, session: Session, entity: ModelT) -> ModelT:
        """Insert a new entity and flush so its PK is populated."""
        session.add(entity)
        session.flush()
        return entity

    def get(self, session: Session, entity_id: int) -> Optional[ModelT]:
        """Return the entity by primary key, or ``None`` if absent."""
        return session.get(self.model, entity_id)

    def list_all(self, session: Session) -> List[ModelT]:
        """Return every row of this entity, unsorted."""
        return list(session.exec(select(self.model)).all())

    def delete(self, session: Session, entity: ModelT) -> None:
        """Mark the entity for deletion on the next commit."""
        session.delete(entity)


class UserDAO(BaseDAO[User]):
    """User lookups — email and username are the two auth entry points."""

    model = User

    def get_by_email(self, session: Session, email: str) -> Optional[User]:
        return session.exec(select(User).where(User.email == email)).first()

    def get_by_username(self, session: Session, username: str) -> Optional[User]:
        return session.exec(select(User).where(User.username == username)).first()


class ProjectDAO(BaseDAO[Project]):
    """Project listings — home page browse + category filter."""

    model = Project

    def list_ordered(
        self, session: Session, category: Optional[Category] = None
    ) -> List[Project]:
        """Return projects newest-first, optionally filtered by category."""
        stmt = select(Project).order_by(Project.created_at.desc())
        if category is not None:
            stmt = stmt.where(Project.category == category)
        return list(session.exec(stmt).all())


class CollectionDAO(BaseDAO[CollectionItem]):
    """Collection lookups — per-user entries and dedup checks."""

    model = CollectionItem

    def get_by_user_and_project(
        self, session: Session, user_id: int, project_id: int
    ) -> Optional[CollectionItem]:
        stmt = select(CollectionItem).where(
            CollectionItem.user_id == user_id,
            CollectionItem.project_id == project_id,
        )
        return session.exec(stmt).first()

    def list_for_user(
        self, session: Session, user_id: int
    ) -> List[CollectionItem]:
        stmt = (
            select(CollectionItem)
            .where(CollectionItem.user_id == user_id)
            .order_by(CollectionItem.added_at.desc())
        )
        return list(session.exec(stmt).all())
