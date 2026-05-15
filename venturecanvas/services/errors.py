"""Typed service-layer exceptions.

Each service class raises one of these when a business rule is
violated; :mod:`venturecanvas.ui.controllers` catches the hierarchy and
translates each concrete type to a user-facing NiceGUI notification.
"""


class ServiceError(Exception):
    """Base class for any business-rule violation raised by a service."""


class ValidationError(ServiceError):
    """Input failed a validation rule (length, format, required field)."""


class AuthError(ServiceError):
    """Authentication failed — wrong credentials or no active session."""


class NotFoundError(ServiceError):
    """The requested entity does not exist."""


class ForbiddenError(ServiceError):
    """Caller is not allowed to perform this action on this entity."""


class DuplicateError(ServiceError):
    """A unique constraint would be violated (duplicate email, etc.)."""
