"""Unit tests — service layer, one business rule per test."""

from __future__ import annotations

import pytest

from venturecanvas.domain.models import Category
from venturecanvas.services.errors import (
    AuthError,
    DuplicateError,
    ValidationError,
)


class TestAuthService:
    def test_register_success(self, auth_service):
        user = auth_service.register("alice", "alice@example.com", "password")
        assert user.id is not None
        assert user.username == "alice"
        assert user.email == "alice@example.com"
        assert user.password_hash != "password"  # must be hashed

    def test_register_duplicate_email(self, auth_service):
        auth_service.register("alice", "alice@example.com", "password")
        with pytest.raises(DuplicateError):
            auth_service.register("alice2", "alice@example.com", "password")

    def test_login_success(self, auth_service):
        auth_service.register("bob", "bob@example.com", "password")
        user = auth_service.authenticate("bob@example.com", "password")
        assert user.username == "bob"

    def test_login_wrong_password(self, auth_service):
        auth_service.register("bob", "bob@example.com", "password")
        with pytest.raises(AuthError):
            auth_service.authenticate("bob@example.com", "wrong")


class TestProjectService:
    @pytest.fixture
    def owner_id(self, auth_service) -> int:
        user = auth_service.register("carol", "carol@example.com", "password")
        return user.id

    def test_create_valid(self, project_service, owner_id):
        project = project_service.create(
            owner_id=owner_id,
            title="Sensor Swarm",
            description="Distributed air-quality mapping.",
            category=Category.IOT,
            required_skills="Python, MQTT",
        )
        assert project.id is not None
        assert project.category is Category.IOT

    def test_create_invalid_title(self, project_service, owner_id):
        with pytest.raises(ValidationError):
            project_service.create(
                owner_id=owner_id,
                title="",  # below min_length=2
                description="anything",
                category=Category.WEB,
            )


class TestCollectionService:
    def test_add_dedup(self, auth_service, project_service, collection_service):
        user = auth_service.register("dan", "dan@example.com", "password")
        project = project_service.create(
            owner_id=user.id,
            title="RAG Bot",
            description="A small RAG app.",
            category=Category.AI,
        )
        collection_service.add(user.id, project.id)
        with pytest.raises(DuplicateError):
            collection_service.add(user.id, project.id)

    def test_summary_aggregates_across_projects(
        self, auth_service, project_service, collection_service
    ):
        user = auth_service.register("eve", "eve@example.com", "password")
        p1 = project_service.create(
            owner_id=user.id,
            title="P1",
            description="d",
            category=Category.AI,
            required_skills="Python, NLP",
            required_tools="LangChain",
        )
        p2 = project_service.create(
            owner_id=user.id,
            title="P2",
            description="d",
            category=Category.WEB,
            required_skills="Python, TypeScript",
            required_tools="Vite",
        )
        collection_service.add(user.id, p1.id)
        collection_service.add(user.id, p2.id)

        summary = collection_service.summary(user.id)

        assert summary["skills"] == ["NLP", "Python", "TypeScript"]
        assert summary["tools"] == ["LangChain", "Vite"]
        # Python must appear exactly once even though it's in both projects.
        assert summary["skills"].count("Python") == 1
