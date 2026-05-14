"""Password hashing utility — stdlib PBKDF2-HMAC-SHA256.

Placed inside ``data_access`` because a hashed password is the at-rest
representation of a secret, which is a persistence concern. Both
:class:`venturecanvas.services.auth_service.AuthService` and
:class:`venturecanvas.data_access.seed.ProjectSeeder` depend on this
class via constructor injection (Plan.md §0.1: no module-level
singletons, no global state).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets


class PasswordHasher:
    """Stateless PBKDF2-HMAC-SHA256 hasher built on stdlib only.

    The stored representation is a single string of the form
    ``"{iterations}${salt_hex}${hash_hex}"``. Everything needed to
    verify a password later is captured in that string, so the
    :class:`~venturecanvas.domain.models.User` schema stays
    single-column and iteration-count bumps are transparent to the
    database.
    """

    DEFAULT_ITERATIONS = 200_000
    _SALT_BYTES = 16

    def __init__(self, iterations: int = DEFAULT_ITERATIONS) -> None:
        if iterations < 1_000:
            raise ValueError("PBKDF2 iterations must be at least 1,000.")
        self._iterations = iterations

    def hash(self, plaintext: str) -> str:
        """Return the storable ``iterations$salt$hash`` representation."""
        salt = secrets.token_bytes(self._SALT_BYTES)
        derived = hashlib.pbkdf2_hmac(
            "sha256", plaintext.encode("utf-8"), salt, self._iterations
        )
        return f"{self._iterations}${salt.hex()}${derived.hex()}"

    def verify(self, plaintext: str, stored: str) -> bool:
        """Return ``True`` iff *plaintext* matches the hash encoded in *stored*."""
        try:
            iterations_str, salt_hex, hash_hex = stored.split("$", 2)
            iterations = int(iterations_str)
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(hash_hex)
        except (ValueError, AttributeError):
            return False
        derived = hashlib.pbkdf2_hmac(
            "sha256", plaintext.encode("utf-8"), salt, iterations
        )
        return hmac.compare_digest(derived, expected)
