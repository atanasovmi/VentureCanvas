"""Authentication service – registration, login, and profile management.

All password handling and user lookup logic is encapsulated here so that
routes remain thin controllers.
"""

from app.extensions import db
from app.models.user import User


def register_user(username: str, email: str, password: str) -> tuple[User | None, str | None]:
    """Create a new user after validating uniqueness.

    Returns:
        (user, None) on success, or (None, error_message) on failure.
    """
    if not username or not email or not password:
        return None, "Username, email, and password are required."

    if User.query.filter_by(email=email).first():
        return None, "Email already registered."

    if User.query.filter_by(username=username).first():
        return None, "Username already taken."

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user, None


def authenticate_user(email: str, password: str) -> tuple[User | None, str | None]:
    """Verify credentials and return the user.

    Returns:
        (user, None) on success, or (None, error_message) on failure.
    """
    if not email or not password:
        return None, "Email and password are required."

    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        return None, "Invalid email or password."

    return user, None


def get_user_by_id(user_id: int) -> User | None:
    """Fetch a user by primary key, or ``None`` if not found."""
    return db.session.get(User, user_id)


def update_user_profile(user_id: int, data: dict) -> tuple[User | None, str | None]:
    """Update mutable profile fields (username, bio).

    Returns:
        (user, None) on success, or (None, error_message) on failure.
    """
    user = db.session.get(User, user_id)
    if user is None:
        return None, "User not found."

    if "username" in data:
        existing = User.query.filter_by(username=data["username"]).first()
        if existing and existing.id != user_id:
            return None, "Username already taken."
        user.username = data["username"]

    if "bio" in data:
        user.bio = data["bio"]

    db.session.commit()
    return user, None
