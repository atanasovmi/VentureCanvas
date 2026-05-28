"""DAO + ORM tests — exercise the persistence layer directly against SQLite."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from venturecanvas.data_access.seed import (
    _SAMPLE_PROJECTS_BY_CATEGORY,
    ProjectSeeder,
)
from venturecanvas.domain.models import Category, CollectionItem, Project, User


class TestProjectDAO:
    def test_project_roundtrip(self, database, user_dao, project_dao):
        with database.session_scope() as session:
            user = User(
                username="alice",
                email="alice@example.com",
                password_hash="1000$" + "a" * 32 + "$" + "b" * 64,
            )
            user_dao.add(session, user)
            project_dao.add(
                session,
                Project(
                    owner_id=user.id,
                    title="Roundtrip",
                    description="Write then read.",
                    category=Category.WEB,
                    required_skills="Python",
                ),
            )

        with database.session_scope() as session:
            projects = project_dao.list_ordered(session)
            assert len(projects) == 1
            assert projects[0].title == "Roundtrip"
            assert projects[0].category is Category.WEB


class TestCollectionUniqueConstraint:
    def test_duplicate_collection_row_raises(
        self, database, user_dao, project_dao, collection_dao
    ):
        with database.session_scope() as session:
            user = User(
                username="bob", email="bob@example.com", password_hash="h"
            )
            user_dao.add(session, user)
            project = Project(
                owner_id=user.id,
                title="Unique",
                description="d",
                category=Category.WEB,
            )
            project_dao.add(session, project)
            collection_dao.add(
                session, CollectionItem(user_id=user.id, project_id=project.id)
            )

        # Second insert violates (user_id, project_id) UniqueConstraint.
        with pytest.raises(IntegrityError):
            with database.session_scope() as session:
                user = user_dao.get_by_email(session, "bob@example.com")
                project = project_dao.list_ordered(session)[0]
                collection_dao.add(
                    session,
                    CollectionItem(user_id=user.id, project_id=project.id),
                )


class TestSeeder:
    def test_seed_is_idempotent_and_populates(self, database, hasher):
        seeder = ProjectSeeder(hasher)

        with database.session_scope() as session:
            assert seeder.is_already_seeded(session) is False
            seeder.seed(session)

        with database.session_scope() as session:
            assert seeder.is_already_seeded(session) is True
            user_count = len(list(session.exec(select(User)).all()))
            project_count = len(list(session.exec(select(Project)).all()))
            assert user_count == 1
            # Derive the expected count from the seed data itself so this
            # assertion self-heals when sample projects are added/removed.
            expected = sum(len(v) for v in _SAMPLE_PROJECTS_BY_CATEGORY.values())
            assert project_count == expected  # every curated sample project
