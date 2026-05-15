"""Service layer — business logic in class-based services.

Every service is a class constructed with its collaborating DAOs (see
Plan.md §0.1: *no module-level CRUD, no singletons, constructor
injection*). Controllers depend on services; services depend on DAOs.

Service methods raise typed exceptions from
:mod:`venturecanvas.services.errors`; controllers catch these and
translate them to user-facing notifications.
"""
