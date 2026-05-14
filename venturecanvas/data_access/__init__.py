"""Persistence layer — Repository / DAO over SQLModel sessions.

Exposes two collaborators the services layer consumes:

* :class:`~venturecanvas.data_access.db.Database` — a Facade over the
  SQLModel engine/session, providing a context-managed ``session_scope``
  and one-shot ``init_schema_and_seed``.
* :class:`~venturecanvas.data_access.dao.BaseDAO` and its per-entity
  subclasses — the Repository / DAO pattern. Services depend on DAOs,
  not on raw sessions, so CRUD calls stay uniform and testable.
"""
