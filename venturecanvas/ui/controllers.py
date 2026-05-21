"""Controller layer of MVC.

One controller class per feature family (Auth, Home, Project,
Collection). Controllers are constructor-injected with the services
and the :class:`~venturecanvas.ui.session_state.SessionState` they
need. Controllers do **not** call NiceGUI — that would couple them to
the UI framework and make unit tests slow. They return plain Python
values or raise typed
:class:`~venturecanvas.services.errors.ServiceError` subclasses; the
pages layer catches these and calls ``ui.notify``.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from ..domain.models import Category, CollectionItem, Project, User
from ..services.auth_service import AuthService
from ..services.collection_service import CollectionService
from ..services.errors import AuthError, ForbiddenError
from ..services.project_service import ProjectService
from .session_state import SessionState


class AuthController:
    """Register / login / logout. Writes the user_id into the SessionState on success."""

    def __init__(
        self,
        auth_service: AuthService,
        session_state: SessionState,
    ) -> None:
        self._auth = auth_service
        self._session = session_state

    def register(self, username: str, email: str, password: str) -> User:
        """Create a new user. Raises ValidationError / DuplicateError on failure."""
        return self._auth.register(username=username, email=email, password=password)

    def login(self, email: str, password: str) -> User:
        """Authenticate and start a session. Raises :class:`AuthError` on failure."""
        user = self._auth.authenticate(email=email, password=password)
        if user.id is None:  # defensive; register always assigns a PK
            raise AuthError("User record has no id.")
        self._session.login(user_id=user.id, username=user.username)
        return user

    def logout(self) -> None:
        """Forget the current browser's login."""
        self._session.logout()

    def current_user(self) -> Optional[User]:
        """Return the authenticated user, or ``None`` if no active session."""
        user_id = self._session.current_user_id()
        if user_id is None:
            return None
        return self._auth.get_user(user_id)

    @property
    def is_authenticated(self) -> bool:
        return self._session.is_authenticated


class HomeController:
    """Home page — list projects, optionally filtered by category."""

    def __init__(self, project_service: ProjectService) -> None:
        self._project_service = project_service

    def list(self, category: Optional[Category] = None) -> List[Project]:
        return self._project_service.list(category=category)

    def available_categories(self) -> List[Category]:
        """Return every category for the filter chips (order matches Plan §3)."""
        return [
            Category.IOT,
            Category.AI,
            Category.WEB,
            Category.MOBILE,
            Category.HARDWARE,
        ]


class ProjectController:
    """Project detail + create / update / delete (ownership enforced in service)."""

    def __init__(
        self,
        project_service: ProjectService,
        session_state: SessionState,
    ) -> None:
        self._project_service = project_service
        self._session = session_state

    def get(self, project_id: int) -> Project:
        """Fetch a project for the detail page. Raises :class:`NotFoundError`."""
        return self._project_service.get(project_id)

    def create(
        self,
        *,
        title: str,
        description: str,
        category: Category,
        required_skills: str = "",
        required_tools: str = "",
        required_apis: str = "",
        required_hardware: str = "",
    ) -> Project:
        """Create a project owned by the logged-in user."""
        owner_id = self._require_user_id()
        return self._project_service.create(
            owner_id=owner_id,
            title=title,
            description=description,
            category=category,
            required_skills=required_skills,
            required_tools=required_tools,
            required_apis=required_apis,
            required_hardware=required_hardware,
        )

    def update(self, project_id: int, **fields: object) -> Project:
        """Update a project owned by the logged-in user."""
        caller_id = self._require_user_id()
        return self._project_service.update(
            project_id=project_id, caller_user_id=caller_id, **fields
        )

    def delete(self, project_id: int) -> None:
        """Delete a project owned by the logged-in user."""
        caller_id = self._require_user_id()
        self._project_service.delete(
            project_id=project_id, caller_user_id=caller_id
        )

    def list_mine(self) -> List[Project]:
        """Return projects owned by the logged-in user, newest first."""
        user_id = self._require_user_id()
        return self._project_service.list(owner_id=user_id)

    def is_owner(self, project: Project) -> bool:
        """True iff the currently-logged-in user owns *project*."""
        current = self._session.current_user_id()
        return current is not None and project.owner_id == current

    def _require_user_id(self) -> int:
        user_id = self._session.current_user_id()
        if user_id is None:
            raise ForbiddenError("You must be logged in to do that.")
        return user_id


class CollectionController:
    """Add / remove / view the logged-in user's collection + aggregation."""

    def __init__(
        self,
        collection_service: CollectionService,
        session_state: SessionState,
    ) -> None:
        self._collection_service = collection_service
        self._session = session_state

    def add(self, project_id: int) -> CollectionItem:
        user_id = self._require_user_id()
        return self._collection_service.add(user_id=user_id, project_id=project_id)

    def remove(self, project_id: int) -> None:
        user_id = self._require_user_id()
        self._collection_service.remove(user_id=user_id, project_id=project_id)

    def view(self) -> tuple[List[Project], Dict[str, List[str]]]:
        """Return the collection's projects and the cross-project resource summary."""
        user_id = self._require_user_id()
        projects = self._collection_service.list_projects(user_id=user_id)
        summary = self._collection_service.summary(user_id=user_id)
        return projects, summary

    def _require_user_id(self) -> int:
        user_id = self._session.current_user_id()
        if user_id is None:
            raise ForbiddenError("You must be logged in to do that.")
        return user_id
