"""Project model representing an innovation idea.

Captures everything a contributor needs to understand and replicate an idea:
description, category, required skills/tools/APIs/hardware, time estimates,
tutorial links, and external resources.
"""

from datetime import datetime, timezone

from app.extensions import db


class Project(db.Model):
    """A community-contributed innovation project."""

    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    time_estimate = db.Column(db.String(100), nullable=True)
    skills_needed = db.Column(db.Text, nullable=True)
    tools_needed = db.Column(db.Text, nullable=True)
    apis_needed = db.Column(db.Text, nullable=True)
    hardware_needed = db.Column(db.Text, nullable=True)
    resources = db.Column(db.Text, nullable=True)
    tutorial_link = db.Column(db.String(500), nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    comments = db.relationship(
        "Comment", backref="project", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        """Serialize the project to a JSON-safe dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "image_url": self.image_url,
            "time_estimate": self.time_estimate,
            "skills_needed": self.skills_needed,
            "tools_needed": self.tools_needed,
            "apis_needed": self.apis_needed,
            "hardware_needed": self.hardware_needed,
            "resources": self.resources,
            "tutorial_link": self.tutorial_link,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "user_id": self.user_id,
            "author": self.author.username if self.author else None,
        }
