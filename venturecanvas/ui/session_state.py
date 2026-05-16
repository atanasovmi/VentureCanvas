"""Per-browser session state for NiceGUI.

This class wraps NiceGUI's ``app.storage.user`` so controllers and pages
work against a small, testable interface instead of poking at the
global storage dict directly. The composition root creates one
instance and injects it into every controller that needs to know who
the caller is.
"""

from __future__ import annotations

from typing import Optional

from nicegui import app


class SessionState:
    """Browser-scoped session state keyed by the NiceGUI storage cookie.

    NiceGUI persists ``app.storage.user`` per-browser (signed cookie),
    so this object has no internal state of its own — it is a thin,
    typed facade over the storage dict. That lets tests substitute a
    plain in-memory implementation with the same interface.
    """

    _KEY_USER_ID = "user_id"
    _KEY_USERNAME = "username"

    def login(self, user_id: int, username: str) -> None:
        """Mark the current browser as logged in as ``user_id`` / ``username``."""
        app.storage.user[self._KEY_USER_ID] = user_id
        app.storage.user[self._KEY_USERNAME] = username

    def logout(self) -> None:
        """Forget the current browser's login."""
        app.storage.user.pop(self._KEY_USER_ID, None)
        app.storage.user.pop(self._KEY_USERNAME, None)

    @property
    def is_authenticated(self) -> bool:
        return self._KEY_USER_ID in app.storage.user

    def current_user_id(self) -> Optional[int]:
        return app.storage.user.get(self._KEY_USER_ID)

    def current_username(self) -> Optional[str]:
        return app.storage.user.get(self._KEY_USERNAME)
