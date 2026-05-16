"""End-to-end flows exercised through the controller layer.

Controllers wrap services + session state, so driving them is the
closest we can get to a real user flow without standing up a NiceGUI
browser session. Plan.md §8 lists three integration scenarios; each
one is its own test.
"""

from __future__ import annotations

import pytest

from venturecanvas.domain.models import Category
from venturecanvas.services.errors import ForbiddenError, NotFoundError


class TestFullUserFlow:
    def test_register_login_create_collect_summary(
        self,
        auth_controller,
        project_controller,
        collection_controller,
    ):
        auth_controller.register(
            username="flo", email="flo@example.com", password="password"
        )
        user = auth_controller.login(email="flo@example.com", password="password")
        assert user.username == "flo"

        project = project_controller.create(
            title="Sensor Swarm",
            description="Distributed air-quality mapping.",
            category=Category.IOT,
            required_skills="Python, MQTT",
            required_tools="ESP32, Mosquitto",
        )
        assert project.id is not None

        collection_controller.add(project.id)

        projects, summary = collection_controller.view()
        assert len(projects) == 1
        assert projects[0].title == "Sensor Swarm"
        assert "Python" in summary["skills"]
        assert "ESP32" in summary["tools"]


class TestProjectOwnership:
    def test_stranger_cannot_edit_others_project(
        self, auth_controller, project_controller
    ):
        auth_controller.register(
            username="owner", email="owner@example.com", password="password"
        )
        auth_controller.login(email="owner@example.com", password="password")
        project = project_controller.create(
            title="Owner's project",
            description="d",
            category=Category.WEB,
        )
        auth_controller.logout()

        auth_controller.register(
            username="stranger",
            email="stranger@example.com",
            password="password",
        )
        auth_controller.login(email="stranger@example.com", password="password")
        with pytest.raises(ForbiddenError):
            project_controller.update(project_id=project.id, title="Hijacked")

    def test_owner_can_edit_then_delete(
        self, auth_controller, project_controller
    ):
        auth_controller.register(
            username="owner", email="owner@example.com", password="password"
        )
        auth_controller.login(email="owner@example.com", password="password")

        project = project_controller.create(
            title="OriginalTitle",
            description="d",
            category=Category.WEB,
        )
        project_controller.update(project_id=project.id, title="UpdatedTitle")
        assert project_controller.get(project.id).title == "UpdatedTitle"

        project_controller.delete(project.id)
        with pytest.raises(NotFoundError):
            project_controller.get(project.id)
