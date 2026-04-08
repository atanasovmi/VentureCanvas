"""Comment service – CRUD operations for project comments.

Comments are always scoped to a project; the service validates that the
parent project exists before creating a comment.
"""

from app.extensions import db
from app.models.comment import Comment
from app.models.project import Project


def list_comments(project_id: int) -> list[dict]:
    """Return all comments for a given project, newest first."""
    project = db.session.get(Project, project_id)
    if project is None:
        return []

    comments = (
        Comment.query
        .filter_by(project_id=project_id)
        .order_by(Comment.created_at.desc())
        .all()
    )
    return [c.to_dict() for c in comments]


def create_comment(
    project_id: int, user_id: int, content: str
) -> tuple[Comment | None, str | None]:
    """Add a comment to a project.

    Returns:
        (comment, None) on success, or (None, error_message) on failure.
    """
    if not content or not content.strip():
        return None, "Comment content is required."

    project = db.session.get(Project, project_id)
    if project is None:
        return None, "Project not found."

    comment = Comment(content=content.strip(), user_id=user_id, project_id=project_id)
    db.session.add(comment)
    db.session.commit()
    return comment, None


def delete_comment(
    comment_id: int, user_id: int
) -> str | None:
    """Delete a comment if owned by *user_id*.

    Returns:
        ``None`` on success, or an error message string.
    """
    comment = db.session.get(Comment, comment_id)
    if comment is None:
        return "Comment not found."
    if comment.user_id != user_id:
        return "Not authorized to delete this comment."

    db.session.delete(comment)
    db.session.commit()
    return None
