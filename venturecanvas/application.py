"""Composition Root — :class:`VentureCanvasApplication`.

The one and only place where objects are constructed and wired
together. Every class further down the call graph declares its
collaborators in ``__init__`` and receives them from here (Plan.md
§0.1: constructor injection, no globals, no singletons elsewhere).

Running the app is a two-step dance::

    VentureCanvasApplication().run()

``run`` asks the :class:`Database` to create the schema and seed the
demo data if the DB is empty, registers every ``@ui.page`` route via
:class:`~venturecanvas.ui.pages.Pages`, and hands control to NiceGUI's
event loop.
"""

from __future__ import annotations

from typing import Optional

from dotenv import load_dotenv
from nicegui import ui

from .data_access.dao import CollectionDAO, ProjectDAO, UserDAO
from .data_access.db import Database
from .data_access.password_hasher import PasswordHasher
from .data_access.seed import ProjectSeeder
from .services.auth_service import AuthService
from .services.collection_service import CollectionService
from .services.project_service import ProjectService
from .ui.controllers import (
    AuthController,
    CollectionController,
    HomeController,
    ProjectController,
)
from .ui.pages import Pages
from .ui.session_state import SessionState


class VentureCanvasApplication:
    """Builds the full object graph and runs NiceGUI.

    ``database`` can be supplied by tests to swap in an in-memory
    SQLite; production code passes nothing and lets the environment
    (or the default project-local ``data/venturecanvas.db``) win.
    """

    DEFAULT_STORAGE_SECRET = "venturecanvas-local-dev"

    def __init__(self, database: Optional[Database] = None) -> None:
        load_dotenv()

        # --- Persistence layer ------------------------------------------------
        self.password_hasher = PasswordHasher()
        self.seeder = ProjectSeeder(self.password_hasher)
        self.database = database or Database(seeder=self.seeder)
        self.database.init_schema_and_seed()

        self.user_dao = UserDAO()
        self.project_dao = ProjectDAO()
        self.collection_dao = CollectionDAO()

        # --- Service layer ---------------------------------------------------
        self.auth_service = AuthService(
            database=self.database,
            user_dao=self.user_dao,
            password_hasher=self.password_hasher,
        )
        self.project_service = ProjectService(
            database=self.database,
            project_dao=self.project_dao,
        )
        self.collection_service = CollectionService(
            database=self.database,
            collection_dao=self.collection_dao,
            project_dao=self.project_dao,
        )

        # --- UI layer --------------------------------------------------------
        self.session_state = SessionState()
        self.auth_controller = AuthController(
            auth_service=self.auth_service,
            session_state=self.session_state,
        )
        self.home_controller = HomeController(project_service=self.project_service)
        self.project_controller = ProjectController(
            project_service=self.project_service,
            session_state=self.session_state,
        )
        self.collection_controller = CollectionController(
            collection_service=self.collection_service,
            session_state=self.session_state,
        )
        self.pages = Pages(
            auth_controller=self.auth_controller,
            home_controller=self.home_controller,
            project_controller=self.project_controller,
            collection_controller=self.collection_controller,
        )

    def run(
        self,
        *,
        host: str = "0.0.0.0",
        port: int = 8080,
        reload: bool = False,
        storage_secret: Optional[str] = None,
    ) -> None:
        """Register routes and start the NiceGUI event loop."""
        self.pages.register()
        ui.run(
            host=host,
            port=port,
            reload=reload,
            storage_secret=storage_secret or self.DEFAULT_STORAGE_SECRET,
            title="VentureCanvas",
        )
