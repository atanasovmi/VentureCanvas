"""Model layer of MVC — SQLModel entity classes and field validation.

The domain layer owns what an object *is* (schema, constraints, simple
invariants). It has no awareness of persistence mechanics or UI state;
both are layered on top by :mod:`venturecanvas.data_access` and
:mod:`venturecanvas.ui`.
"""
