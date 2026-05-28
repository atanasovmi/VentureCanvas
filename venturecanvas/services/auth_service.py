"""Authentication service — registration and login.

:class:`AuthService` is the only place plaintext passwords are handled;
it delegates hashing to
:class:`venturecanvas.data_access.password_hasher.PasswordHasher` and
persistence to :class:`venturecanvas.data_access.dao.UserDAO`. Logout
is a pure UI-state operation and lives in
:class:`venturecanvas.ui.session_state.SessionState`.

Because :class:`~venturecanvas.domain.models.User` is a ``table=True``
SQLModel — which skips pydantic ``Field`` validation at construction —
this service is also where the username, email and password rules
declared on the model are actually enforced at runtime.
"""

from __future__ import annotations

from typing import Optional

from ..data_access.dao import UserDAO
from ..data_access.db import Database
from ..data_access.password_hasher import PasswordHasher
from ..domain.models import User
from .errors import AuthError, DuplicateError, ValidationError


class AuthService:
    """Business logic for user registration and login.

    Constructor-injected with the :class:`Database` facade (for
    session_scope), the :class:`UserDAO` (for user lookups), and the
    :class:`PasswordHasher` (for hashing / verification).
    """

    MIN_PASSWORD_LENGTH = 6

    # Mirror the Field(...) bounds declared on the User model. table=True
    # models don't self-validate (see register), so these constants are the
    # runtime source for the same numbers the schema documents.
    MIN_USERNAME_LENGTH = 3
    MAX_USERNAME_LENGTH = 40
    MAX_EMAIL_LENGTH = 120

    def __init__(
        self,
        database: Database,
        user_dao: UserDAO,
        password_hasher: PasswordHasher,
    ) -> None:
        self._db = database
        self._user_dao = user_dao
        self._hasher = password_hasher

    def register(self, username: str, email: str, password: str) -> User:
        """Create a new user and return it.

        Raises :class:`ValidationError` on bad input, :class:`DuplicateError`
        if the email or username is already taken.

        Input is normalised (trim username, trim + lowercase email) and then
        validated here, before any DB work. The ``User`` model's
        ``Field(...)`` constraints can't do this for us — ``table=True``
        models skip pydantic validation — so the length/format checks live
        in this service. The database still guarantees uniqueness.
        """
        username_norm = (username or "").strip()
        email_norm = (email or "").strip().lower()
        self._validate_username(username_norm)
        self._validate_email(email_norm)
        self._validate_password(password)

        with self._db.session_scope() as session:
            if self._user_dao.get_by_email(session, email_norm) is not None:
                raise DuplicateError("An account with this email already exists.")
            if self._user_dao.get_by_username(session, username_norm) is not None:
                raise DuplicateError("This username is already taken.")

            user = User(
                username=username_norm,
                email=email_norm,
                password_hash=self._hasher.hash(password),
            )
            self._user_dao.add(session, user)
            return user

    def authenticate(self, email: str, password: str) -> User:
        """Return the user matching *email* / *password* or raise :class:`AuthError`."""
        email_norm = (email or "").strip().lower()   # match how register stored it
        with self._db.session_scope() as session:
            user = self._user_dao.get_by_email(session, email_norm)
            # One generic message for both "no such email" and "wrong password",
            # so we never reveal which accounts exist.
            if user is None or not self._hasher.verify(password, user.password_hash):
                raise AuthError("Invalid email or password.")
            return user

    def get_user(self, user_id: int) -> Optional[User]:
        """Look up a user by id — used by controllers to display the current user."""
        with self._db.session_scope() as session:
            return self._user_dao.get(session, user_id)

    def _validate_username(self, username: str) -> None:
        """Length-check the already-trimmed username (model bound: 3–40)."""
        if len(username) < self.MIN_USERNAME_LENGTH:
            raise ValidationError(
                f"Username must be at least {self.MIN_USERNAME_LENGTH} characters long."
            )
        if len(username) > self.MAX_USERNAME_LENGTH:
            raise ValidationError(
                f"Username cannot exceed {self.MAX_USERNAME_LENGTH} characters."
            )

    def _validate_email(self, email: str) -> None:
        """Lightweight sanity check on the already-normalised email.

        Deliberately *not* a full RFC validator — Plan.md §2 forbids extra
        validator libraries. We require a single ``@`` with a non-empty
        local part and a dotted domain, within the 120-char column bound.
        That rejects the obvious garbage ("", ``foo``, ``a@b``) while
        staying simple; uniqueness is enforced separately by the DB.
        """
        if not email:
            raise ValidationError("Email is required.")
        if len(email) > self.MAX_EMAIL_LENGTH:
            raise ValidationError(
                f"Email cannot exceed {self.MAX_EMAIL_LENGTH} characters."
            )
        local, sep, domain = email.partition("@")
        if not sep or not local or "@" in domain or "." not in domain:
            raise ValidationError("Please enter a valid email address.")

    def _validate_password(self, password: str) -> None:
        if password is None or len(password) < self.MIN_PASSWORD_LENGTH:
            raise ValidationError(
                f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters long."
            )
