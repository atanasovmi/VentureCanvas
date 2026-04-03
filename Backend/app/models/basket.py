"""Basket models – lets users save projects for later.

A basket is implicitly per-user; ``BasketItem`` links a user to a project
with a unique constraint so the same project cannot appear twice.
"""

from datetime import datetime, timezone

from app.extensions import db


class BasketItem(db.Model):
    """An association between a user and a saved project."""

    __tablename__ = "basket_items"
    __table_args__ = (
        db.UniqueConstraint("user_id", "project_id", name="uq_user_project"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id"), nullable=False
    )
    added_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship("User", backref="basket_items")
    project = db.relationship("Project", backref="basket_items")

    def to_dict(self) -> dict:
        """Serialize the basket item including nested project details."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "project": self.project.to_dict() if self.project else None,
        }
