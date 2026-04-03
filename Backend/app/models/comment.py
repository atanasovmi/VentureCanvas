"""Comment model for project discussions.

Each comment is tied to exactly one project and one author.
"""

from datetime import datetime, timezone

from app.extensions import db


class Comment(db.Model):
    """A user comment on a project."""

    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id"), nullable=False
    )

    def to_dict(self) -> dict:
        """Serialize the comment to a JSON-safe dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "author": self.author.username if self.author else None,
        }
