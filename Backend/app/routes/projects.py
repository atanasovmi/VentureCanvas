"""Project routes – CRUD with search and category filtering.

All endpoints live under ``/api/projects``.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.services import project_service

projects_bp = Blueprint("projects", __name__, url_prefix="/api/projects")


@projects_bp.route("", methods=["GET"])
def list_projects():
    """Return a paginated list of projects, with optional search and category filters."""
    search = request.args.get("search")
    category = request.args.get("category")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    result = project_service.list_projects(
        search=search, category=category, page=page, per_page=per_page
    )
    return jsonify({"message": "Projects retrieved.", "data": result}), 200


@projects_bp.route("/<int:project_id>", methods=["GET"])
def get_project(project_id: int):
    """Return a single project by ID."""
    project = project_service.get_project(project_id)
    if project is None:
        return jsonify({"message": "Project not found."}), 404

    return jsonify({"message": "Project retrieved.", "data": project.to_dict()}), 200


@projects_bp.route("", methods=["POST"])
@jwt_required()
def create_project():
    """Create a new project (requires JWT)."""
    data = request.get_json(silent=True) or {}
    project, error = project_service.create_project(int(get_jwt_identity()), data)
    if error:
        return jsonify({"message": error}), 400

    return jsonify({"message": "Project created.", "data": project.to_dict()}), 201


@projects_bp.route("/<int:project_id>", methods=["PUT"])
@jwt_required()
def update_project(project_id: int):
    """Update an existing project (owner only)."""
    data = request.get_json(silent=True) or {}
    project, error = project_service.update_project(
        project_id, int(get_jwt_identity()), data
    )
    if error:
        status = 404 if "not found" in error.lower() else 403
        return jsonify({"message": error}), status

    return jsonify({"message": "Project updated.", "data": project.to_dict()}), 200


@projects_bp.route("/<int:project_id>", methods=["DELETE"])
@jwt_required()
def delete_project(project_id: int):
    """Delete a project (owner only)."""
    error = project_service.delete_project(project_id, int(get_jwt_identity()))
    if error:
        status = 404 if "not found" in error.lower() else 403
        return jsonify({"message": error}), status

    return jsonify({"message": "Project deleted."}), 200
