"""Project service – CRUD and search/filter logic for projects.

Handles pagination, keyword search across title/description, and category
filtering so the route layer stays declarative.
"""

from app.extensions import db
from app.models.project import Project


def list_projects(
    search: str | None = None,
    category: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> dict:
    """Return a paginated, optionally filtered list of projects.

    Args:
        search: Case-insensitive substring match on title or description.
        category: Exact category filter.
        page: 1-based page number.
        per_page: Items per page.

    Returns:
        Dict with ``items``, ``total``, ``page``, and ``pages`` keys.
    """
    query = Project.query

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            db.or_(
                Project.title.ilike(pattern),
                Project.description.ilike(pattern),
            )
        )

    if category:
        query = query.filter_by(category=category)

    query = query.order_by(Project.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return {
        "items": [p.to_dict() for p in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
    }


def get_project(project_id: int) -> Project | None:
    """Fetch a single project by ID, or ``None``."""
    return db.session.get(Project, project_id)


def create_project(user_id: int, data: dict) -> tuple[Project | None, str | None]:
    """Persist a new project.

    Returns:
        (project, None) on success, or (None, error_message) on failure.
    """
    if not data.get("title") or not data.get("description"):
        return None, "Title and description are required."

    project = Project(
        title=data["title"],
        description=data["description"],
        category=data.get("category"),
        image_url=data.get("image_url"),
        time_estimate=data.get("time_estimate"),
        skills_needed=data.get("skills_needed"),
        tools_needed=data.get("tools_needed"),
        apis_needed=data.get("apis_needed"),
        hardware_needed=data.get("hardware_needed"),
        resources=data.get("resources"),
        tutorial_link=data.get("tutorial_link"),
        user_id=user_id,
    )
    db.session.add(project)
    db.session.commit()
    return project, None


def update_project(
    project_id: int, user_id: int, data: dict
) -> tuple[Project | None, str | None]:
    """Update an existing project owned by *user_id*.

    Returns:
        (project, None) on success, or (None, error_message) on failure.
    """
    project = db.session.get(Project, project_id)
    if project is None:
        return None, "Project not found."
    if project.user_id != user_id:
        return None, "Not authorized to update this project."

    updatable = [
        "title", "description", "category", "image_url", "time_estimate",
        "skills_needed", "tools_needed", "apis_needed", "hardware_needed",
        "resources", "tutorial_link",
    ]
    for field in updatable:
        if field in data:
            setattr(project, field, data[field])

    db.session.commit()
    return project, None


def delete_project(project_id: int, user_id: int) -> str | None:
    """Delete a project if owned by *user_id*.

    Returns:
        ``None`` on success, or an error message string.
    """
    project = db.session.get(Project, project_id)
    if project is None:
        return "Project not found."
    if project.user_id != user_id:
        return "Not authorized to delete this project."

    db.session.delete(project)
    db.session.commit()
    return None
