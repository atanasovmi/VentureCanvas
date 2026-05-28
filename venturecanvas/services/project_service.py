"""Project service — CRUD with ownership checks.

All write operations verify that the caller owns the target project;
the controller layer never does this check itself. Creation and editing
coerce the category through :class:`Category`, so a value outside the
five-chip set is rejected at the service boundary rather than being
stored silently — a ``table=True`` model won't reject it on its own.
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

    Validation lives here, not on the model. SQLModel's ``table=True``
    models skip pydantic validation at construction time, so this class
    re-checks every user-facing rule before persisting: title and
    description length, the four comma-separated requirement lists, and
    the category enum. The ``Field(...)`` declarations on
    :class:`~venturecanvas.domain.models.Project` remain the single
    declarative source of truth for those bounds; this class is the
    execution point.
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
    _REQUIRED_MAX = 300  # mirrors Project.required_* Field(max_length=300)

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

    def list_filtered(
        self,
        *,
        category: Optional[Category] = None,
        search: str = "",
        sort: str = "newest",
        owner_id: Optional[int] = None,
    ) -> List[Project]:
        """Browse-page query with case-insensitive search and a sort knob.

        Filtering happens in Python on top of :meth:`list`. At demo scale
        (~50 rows) the cost is microseconds; pushing search into SQL is
        a localised change behind this method when the row count grows.
        """
        rows = self.list(category=category, owner_id=owner_id)
        if search:
            q = search.strip().lower()
            if q:
                rows = [
                    p for p in rows
                    if q in p.title.lower() or q in p.description.lower()
                ]
        if sort == "oldest":
            rows = list(reversed(rows))
        elif sort == "az":
            rows = sorted(rows, key=lambda p: p.title.lower())
        return rows

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
        category = self._coerce_category(category)
        self._validate_requirements(
            required_skills=required_skills or "",
            required_tools=required_tools or "",
            required_apis=required_apis or "",
            required_hardware=required_hardware or "",
        )

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
            # Bound only the requirement lists actually supplied, so a
            # partial edit (e.g. title-only) is left untouched.
            self._validate_requirements(
                **{
                    name: str(fields[name])
                    for name in (
                        "required_skills",
                        "required_tools",
                        "required_apis",
                        "required_hardware",
                    )
                    if name in fields and fields[name] is not None
                }
            )

            for field_name in self._UPDATABLE_FIELDS:
                if field_name in fields and fields[field_name] is not None:
                    value = fields[field_name]
                    if field_name in {"title", "description"} and isinstance(value, str):
                        value = value.strip()
                    elif field_name == "category":
                        value = self._coerce_category(value)
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

    def _coerce_category(self, value: object) -> Category:
        """Return *value* as a :class:`Category`, rejecting anything else.

        ``Category(value)`` is idempotent for an existing member, so the UI
        (which already hands us a :class:`Category`) is unaffected. A stray
        string from a non-UI caller raises :class:`ValidationError` instead
        of being persisted unchecked — a ``table=True`` model accepts it
        silently otherwise.
        """
        try:
            return Category(value)
        except ValueError as exc:
            raise ValidationError("Unknown project category.") from exc

    def _validate_requirements(
        self,
        *,
        required_skills: str = "",
        required_tools: str = "",
        required_apis: str = "",
        required_hardware: str = "",
    ) -> None:
        """Bound each comma-separated requirement list to the model's max_length."""
        for label, value in (
            ("Skills", required_skills),
            ("Tools", required_tools),
            ("APIs", required_apis),
            ("Hardware", required_hardware),
        ):
            if len(value or "") > self._REQUIRED_MAX:
                raise ValidationError(
                    f"{label} cannot exceed {self._REQUIRED_MAX} characters."
                )

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
