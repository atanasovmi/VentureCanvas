"""Collection service — add/remove + cross-project resource aggregation.

The aggregation (Plan.md §3 feature 12) is the one bit of real business
logic in the app: split every saved project's comma-separated
requirements, union the tokens into a per-category set, and return a
sorted view. That logic lives here, not in the controller or DAO, so it
is independently testable.
"""

from __future__ import annotations

from typing import Dict, List

from ..data_access.dao import CollectionDAO, ProjectDAO
from ..data_access.db import Database
from ..domain.models import CollectionItem, Project
from .errors import DuplicateError, NotFoundError


class CollectionService:
    """Business logic for the per-user project collection."""

    def __init__(
        self,
        database: Database,
        collection_dao: CollectionDAO,
        project_dao: ProjectDAO,
    ) -> None:
        self._db = database
        self._collection_dao = collection_dao
        self._project_dao = project_dao

    def add(self, user_id: int, project_id: int) -> CollectionItem:
        """Add a project to the user's collection.

        Raises :class:`NotFoundError` if the project does not exist and
        :class:`DuplicateError` if it is already in the collection.
        """
        with self._db.session_scope() as session:
            project = self._project_dao.get(session, project_id)
            if project is None:
                raise NotFoundError("Project not found.")
            existing = self._collection_dao.get_by_user_and_project(
                session, user_id=user_id, project_id=project_id
            )
            if existing is not None:
                raise DuplicateError("This project is already in your collection.")
            item = CollectionItem(user_id=user_id, project_id=project_id)
            self._collection_dao.add(session, item)
            return item

    def remove(self, user_id: int, project_id: int) -> None:
        """Remove a project from the user's collection, or raise :class:`NotFoundError`."""
        with self._db.session_scope() as session:
            item = self._collection_dao.get_by_user_and_project(
                session, user_id=user_id, project_id=project_id
            )
            if item is None:
                raise NotFoundError("This project is not in your collection.")
            self._collection_dao.delete(session, item)

    def list_projects(self, user_id: int) -> List[Project]:
        """Return the :class:`Project` objects currently in ``user_id``'s collection."""
        with self._db.session_scope() as session:
            items = self._collection_dao.list_for_user(session, user_id=user_id)
            # Materialise the related Project up-front so callers can
            # read attributes after the session closes.
            return [item.project for item in items if item.project is not None]

    def summary(self, user_id: int) -> Dict[str, List[str]]:
        """Return the union of every required_* field across the user's collection.

        Keys: ``skills``, ``tools``, ``apis``, ``hardware``. Each value
        is a sorted list of unique tokens, ready for the UI to render as
        chips. An empty collection returns empty lists under every key.
        """
        projects = self.list_projects(user_id)
        skills: set[str] = set()
        tools: set[str] = set()
        apis: set[str] = set()
        hardware: set[str] = set()
        for project in projects:
            skills.update(self._split_tags(project.required_skills))
            tools.update(self._split_tags(project.required_tools))
            apis.update(self._split_tags(project.required_apis))
            hardware.update(self._split_tags(project.required_hardware))
        return {
            "skills": sorted(skills),
            "tools": sorted(tools),
            "apis": sorted(apis),
            "hardware": sorted(hardware),
        }

    @staticmethod
    def _split_tags(value: str) -> List[str]:
        """Split a comma-separated requirement list into stripped, non-empty tokens."""
        if not value:
            return []
        return [token.strip() for token in value.split(",") if token.strip()]
