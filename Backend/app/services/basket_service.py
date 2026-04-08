"""Basket service – save / unsave projects for a user.

The basket acts as a personal bookmarking list.  A unique constraint
prevents duplicates at the database level, but we also check in code to
return a friendly message.
"""

from app.extensions import db
from app.models.basket import BasketItem
from app.models.project import Project


def get_basket(user_id: int) -> dict:
    """Return the user's basket items with an aggregated resource summary.

    The summary collects all unique skills, tools, APIs, hardware, and
    resources across every saved project so users can see what they need
    at a glance.
    """
    items = BasketItem.query.filter_by(user_id=user_id).all()

    skills: set[str] = set()
    tools: set[str] = set()
    apis: set[str] = set()
    hardware: set[str] = set()
    resources: set[str] = set()

    for item in items:
        project = item.project
        if project:
            for val in _split(project.skills_needed):
                skills.add(val)
            for val in _split(project.tools_needed):
                tools.add(val)
            for val in _split(project.apis_needed):
                apis.add(val)
            for val in _split(project.hardware_needed):
                hardware.add(val)
            for val in _split(project.resources):
                resources.add(val)

    return {
        "items": [i.to_dict() for i in items],
        "summary": {
            "skills": sorted(skills),
            "tools": sorted(tools),
            "apis": sorted(apis),
            "hardware": sorted(hardware),
            "resources": sorted(resources),
        },
    }


def add_to_basket(user_id: int, project_id: int) -> tuple[BasketItem | None, str | None]:
    """Add a project to the user's basket.

    Returns:
        (basket_item, None) on success, or (None, error_message) on failure.
    """
    project = db.session.get(Project, project_id)
    if project is None:
        return None, "Project not found."

    existing = BasketItem.query.filter_by(
        user_id=user_id, project_id=project_id
    ).first()
    if existing:
        return None, "Project already in basket."

    item = BasketItem(user_id=user_id, project_id=project_id)
    db.session.add(item)
    db.session.commit()
    return item, None


def remove_from_basket(user_id: int, project_id: int) -> str | None:
    """Remove a project from the user's basket.

    Returns:
        ``None`` on success, or an error message string.
    """
    item = BasketItem.query.filter_by(
        user_id=user_id, project_id=project_id
    ).first()
    if item is None:
        return "Item not found in basket."

    db.session.delete(item)
    db.session.commit()
    return None


def _split(value: str | None) -> list[str]:
    """Split a comma-separated string into stripped, non-empty tokens."""
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]
