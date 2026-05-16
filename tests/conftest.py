"""Shared pytest fixtures — fresh SQLite DB + fully-wired services and controllers.

Every test gets its own file-backed SQLite via :func:`tmp_path`, so state
never leaks between tests. NiceGUI's ``SessionState`` is substituted
with :class:`InMemorySessionState` so controller tests can run without
a browser.
"""

from __future__ import annotations

from typing import Optional

import pytest

from venturecanvas.data_access.dao import CollectionDAO, ProjectDAO, UserDAO
from venturecanvas.data_access.db import Database
from venturecanvas.data_access.password_hasher import PasswordHasher
from venturecanvas.services.auth_service import AuthService
from venturecanvas.services.collection_service import CollectionService
from venturecanvas.services.project_service import ProjectService
from venturecanvas.ui.controllers import (
    AuthController,
    CollectionController,
    HomeController,
    ProjectController,
)


class InMemorySessionState:
    """Test double for :class:`venturecanvas.ui.session_state.SessionState`.

    Implements the same duck-typed surface the controllers rely on, but
    stores the user_id in a plain attribute instead of NiceGUI's
    browser-backed ``app.storage.user``.
    """

    def __init__(self) -> None:
        self._user_id: Optional[int] = None
        self._username: Optional[str] = None

    def login(self, user_id: int, username: str) -> None:
        self._user_id = user_id
        self._username = username

    def logout(self) -> None:
        self._user_id = None
        self._username = None

    @property
    def is_authenticated(self) -> bool:
        return self._user_id is not None

    def current_user_id(self) -> Optional[int]:
        return self._user_id

    def current_username(self) -> Optional[str]:
        return self._username


@pytest.fixture
def database(tmp_path) -> Database:
    """Per-test SQLite DB (file-backed so SQLAlchemy's pool is happy)."""
    url = f"sqlite:///{tmp_path / 'test.db'}"
    db = Database(database_url=url)
    db.init_schema_and_seed()
    return db


@pytest.fixture
def hasher() -> PasswordHasher:
    """Low-iteration PBKDF2 so tests run fast — still above the 1k minimum."""
    return PasswordHasher(iterations=1000)


@pytest.fixture
def user_dao() -> UserDAO:
    return UserDAO()


@pytest.fixture
def project_dao() -> ProjectDAO:
    return ProjectDAO()


@pytest.fixture
def collection_dao() -> CollectionDAO:
    return CollectionDAO()


@pytest.fixture
def auth_service(database, user_dao, hasher) -> AuthService:
    return AuthService(database=database, user_dao=user_dao, password_hasher=hasher)


@pytest.fixture
def project_service(database, project_dao) -> ProjectService:
    return ProjectService(database=database, project_dao=project_dao)


@pytest.fixture
def collection_service(database, collection_dao, project_dao) -> CollectionService:
    return CollectionService(
        database=database,
        collection_dao=collection_dao,
        project_dao=project_dao,
    )


@pytest.fixture
def session_state() -> InMemorySessionState:
    return InMemorySessionState()


@pytest.fixture
def auth_controller(auth_service, session_state) -> AuthController:
    return AuthController(auth_service=auth_service, session_state=session_state)


@pytest.fixture
def home_controller(project_service) -> HomeController:
    return HomeController(project_service=project_service)


@pytest.fixture
def project_controller(project_service, session_state) -> ProjectController:
    return ProjectController(
        project_service=project_service, session_state=session_state
    )


@pytest.fixture
def collection_controller(
    collection_service, session_state
) -> CollectionController:
    return CollectionController(
        collection_service=collection_service,
        session_state=session_state,
    )
