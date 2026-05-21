"""Project service — CRUD with ownership checks.

All write operations verify that the caller owns the target project;
the controller layer never does this check itself. The category
parameter is typed as :class:`Category`, so filtering and creation both
reject values outside the five-chip set at the service boundary.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from ..data_access.dao import ProjectDAO
from ..data_access.db import Database
from ..domain.models import Category, Project
from .errors import ForbiddenError, NotFoundError, ValidationError


class ProjectService:
    """Business logic for browsing, creating, editing and deleting projects.

    Validation lives here *as well as* on the
    :class:`~venturecanvas.domain.models.Project` ``Field(...)``
    declarations: SQLModel's ``table=True`` models skip pydantic
    validation at construction time, so we enforce the same rules
    defensively in the service. Field() remains the single declarative
    source of truth; this class is the execution point.
    """

    _UPDATABLE_FIELDS = (
        "title",
        "description",
        "category",
        "required_skills",
        "required_tools",
        "required_apis",
        "required_hardware",
    )

    _TITLE_MIN = 2
    _TITLE_MAX = 200
    _DESCRIPTION_MIN = 1
    _DESCRIPTION_MAX = 2000

    def __init__(self, database: Database, project_dao: ProjectDAO) -> None:
        self._db = database
        self._project_dao = project_dao

    def list(
        self,
        category: Optional[Category] = None,
        owner_id: Optional[int] = None,
    ) -> List[Project]:
        """Return projects newest-first, optionally filtered by category and/or owner."""
        with self._db.session_scope() as session:
            return self._project_dao.list_ordered(
                session, category=category, owner_id=owner_id
            )

    def get(self, project_id: int) -> Project:
        """Fetch one project by id or raise :class:`NotFoundError`."""
        with self._db.session_scope() as session:
            project = self._project_dao.get(session, project_id)
            if project is None:
                raise NotFoundError("Project not found.")
            return project

    def create(
        self,
        owner_id: int,
        *,
        title: str,
        description: str,
        category: Category,
        required_skills: str = "",
        required_tools: str = "",
        required_apis: str = "",
        required_hardware: str = "",
    ) -> Project:
        """Persist a new project authored by ``owner_id``."""
        self._validate_title(title)
        self._validate_description(description)

        project = Project(
            owner_id=owner_id,
            title=title.strip(),
            description=description.strip(),
            category=category,
            required_skills=required_skills or "",
            required_tools=required_tools or "",
            required_apis=required_apis or "",
            required_hardware=required_hardware or "",
        )

        with self._db.session_scope() as session:
            self._project_dao.add(session, project)
            return project

    def update(
        self,
        project_id: int,
        caller_user_id: int,
        **fields: object,
    ) -> Project:
        """Update a project owned by ``caller_user_id``.

        Only keys listed in :attr:`_UPDATABLE_FIELDS` are applied; unknown
        keys are silently ignored so a stray form field cannot overwrite
        ``owner_id``, ``id``, or the ``created_at`` timestamp.
        """
        with self._db.session_scope() as session:
            project = self._project_dao.get(session, project_id)
            if project is None:
                raise NotFoundError("Project not found.")
            if project.owner_id != caller_user_id:
                raise ForbiddenError("You can only edit your own projects.")

            if "title" in fields and fields["title"] is not None:
                self._validate_title(str(fields["title"]))
            if "description" in fields and fields["description"] is not None:
                self._validate_description(str(fields["description"]))

            for field_name in self._UPDATABLE_FIELDS:
                if field_name in fields and fields[field_name] is not None:
                    value = fields[field_name]
                    if field_name in {"title", "description"} and isinstance(value, str):
                        value = value.strip()
                    setattr(project, field_name, value)
            project.updated_at = datetime.now(timezone.utc)
            return project

    def delete(self, project_id: int, caller_user_id: int) -> None:
        """Delete a project owned by ``caller_user_id``.

        Cascades to collection_items via the SQLModel relationship so no
        orphan rows are left behind.
        """
        with self._db.session_scope() as session:
            project = self._project_dao.get(session, project_id)
            if project is None:
                raise NotFoundError("Project not found.")
            if project.owner_id != caller_user_id:
                raise ForbiddenError("You can only delete your own projects.")
            self._project_dao.delete(session, project)

    # ------------------------------------------------------------------ validation

    def _validate_title(self, title: str) -> None:
        stripped = (title or "").strip()
        if len(stripped) < self._TITLE_MIN:
            raise ValidationError(
                f"Title must be at least {self._TITLE_MIN} characters long."
            )
        if len(stripped) > self._TITLE_MAX:
            raise ValidationError(
                f"Title cannot exceed {self._TITLE_MAX} characters."
            )

    def _validate_description(self, description: str) -> None:
        stripped = (description or "").strip()
        if len(stripped) < self._DESCRIPTION_MIN:
            raise ValidationError("Description is required.")
        if len(stripped) > self._DESCRIPTION_MAX:
            raise ValidationError(
                f"Description cannot exceed {self._DESCRIPTION_MAX} characters."
            )
