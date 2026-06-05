"""Facade pattern — Database wraps the SQLModel engine.

Services depend on :class:`Database` to open a transactional session
(via :meth:`session_scope`) and on the DAOs in
:mod:`venturecanvas.data_access.dao` to query inside that session.
``Database`` owns one engine for the lifetime of the application and
is constructed once in
:class:`venturecanvas.application.VentureCanvasApplication`.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional, Protocol

from sqlalchemy.engine import Engine, make_url
from sqlmodel import Session, SQLModel, create_engine


class _Seeder(Protocol):
    """Duck-typed seeder the Database runs after creating the schema."""

    def is_already_seeded(self, session: Session) -> bool: ...

    def seed(self, session: Session) -> None: ...


class Database:
    """Facade over the SQLModel engine with session + schema management.

    Given a ``database_url`` (or falling back to the ``DATABASE_URL`` env
    var, or a project-local SQLite file), ``Database`` owns one engine
    for the app's lifetime. Callers never touch the engine directly —
    they open a :meth:`session_scope` unit-of-work and pass the session
    to DAOs.
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        *,
        seeder: Optional[_Seeder] = None,
        echo: bool = False,
    ) -> None:
        self._database_url = (
            database_url
            or os.getenv("DATABASE_URL")
            or self._default_sqlite_url()
        )
        self._ensure_sqlite_dir(self._database_url)
        # check_same_thread=False is required because NiceGUI serves
        # requests from a worker thread pool.
        self._engine: Engine = create_engine(
            self._database_url,
            echo=echo,
            connect_args={"check_same_thread": False},
        )
        self._seeder = seeder

    @staticmethod
    def _default_sqlite_url() -> str:
        return "sqlite:///data/venturecanvas.db"

    @staticmethod
    def _ensure_sqlite_dir(database_url: str) -> None:
        """Create the parent directory of a file-backed SQLite URL.

        SQLite creates a missing database *file* on first connect, but
        never a missing *directory* — without this, any DATABASE_URL
        pointing into a not-yet-existing folder (e.g. ``data/`` on a
        fresh clone) fails with "unable to open database file".
        """
        url = make_url(database_url)
        if (
            url.get_backend_name() == "sqlite"
            and url.database
            and url.database != ":memory:"
        ):
            Path(url.database).parent.mkdir(parents=True, exist_ok=True)

    @property
    def engine(self) -> Engine:
        return self._engine

    def init_schema_and_seed(self) -> None:
        """Create all tables; if a seeder is wired in and the DB is empty, run it."""
        SQLModel.metadata.create_all(self._engine)   # CREATE TABLE for every model (no-op if they exist)
        if self._seeder is None:                      # tests pass no seeder → empty DB
            return
        with self.session_scope() as session:
            if not self._seeder.is_already_seeded(session):  # idempotent: seed only once
                self._seeder.seed(session)

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        """Yield a Session wrapped in commit-on-success / rollback-on-error.

        ``expire_on_commit=False`` keeps loaded attributes available on
        entities returned *from* the context manager — services can hand
        the resulting object back to a controller without a second
        round-trip.
        """
        session = Session(self._engine, expire_on_commit=False)
        try:
            yield session         # caller runs all its DAO calls inside this block
            session.commit()      # success path: persist everything atomically
        except Exception:
            session.rollback()    # any error → undo the whole unit of work
            raise                 # re-raise so the service/UI can react
        finally:
            session.close()       # always release the connection
