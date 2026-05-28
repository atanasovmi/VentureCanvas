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
        salt = secrets.token_bytes(self._SALT_BYTES)   # fresh random salt per password
        derived = hashlib.pbkdf2_hmac(                 # slow, salted one-way derivation
            "sha256", plaintext.encode("utf-8"), salt, self._iterations
        )
        # Pack everything verify() needs into one column: cost, salt, and digest.
        return f"{self._iterations}${salt.hex()}${derived.hex()}"

    def verify(self, plaintext: str, stored: str) -> bool:
        """Return ``True`` iff *plaintext* matches the hash encoded in *stored*.

        Total by contract: a malformed ``stored`` string, a non-positive
        iteration count, or a ``None``/non-string *plaintext* all yield
        ``False`` rather than raising, so the auth service can treat a wrong
        password and a corrupt row identically. The whole derivation lives
        inside the ``try`` for that reason — ``pbkdf2_hmac`` itself rejects
        a zero/negative work factor, and ``None.encode`` raises.
        """
        try:
            # Unpack the three fields we packed in hash().
            iterations_str, salt_hex, hash_hex = stored.split("$", 2)
            iterations = int(iterations_str)
            if iterations < 1:
                return False
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(hash_hex)
            # Re-derive with the SAME salt + cost; a matching password yields
            # the same bytes.
            derived = hashlib.pbkdf2_hmac(
                "sha256", plaintext.encode("utf-8"), salt, iterations
            )
        except (ValueError, AttributeError):
            return False
        # Constant-time compare to avoid leaking match info via timing.
        return hmac.compare_digest(derived, expected)
