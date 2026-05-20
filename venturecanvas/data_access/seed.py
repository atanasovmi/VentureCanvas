"""Idempotent demo-data seeder.

Runs once on the first app launch (Plan.md §12). Creates one demo user
and six curated projects spanning the five categories — just enough
material for the home page, category filter, detail view, collection,
and aggregation to have something to show during the live demo.
"""

from __future__ import annotations

from typing import Sequence

from sqlmodel import Session, select

from ..domain.models import Category, Project, User
from .password_hasher import PasswordHasher


class ProjectSeeder:
    """Seeds the demo user plus six sample projects.

    Instantiated by the composition root with a
    :class:`PasswordHasher`, so the demo user's password is hashed with
    exactly the same routine as every live registration.
    """

    DEMO_EMAIL = "admin@venturecanvas.com"
    DEMO_USERNAME = "admin"
    DEMO_PASSWORD = "admin123"  # noqa: S105 — well-known demo credential

    def __init__(self, password_hasher: PasswordHasher) -> None:
        self._hasher = password_hasher

    def is_already_seeded(self, session: Session) -> bool:
        """True iff the demo user already exists — keeps seeding idempotent."""
        existing = session.exec(
            select(User).where(User.email == self.DEMO_EMAIL)
        ).first()
        return existing is not None

    def seed(self, session: Session) -> None:
        """Insert the demo user and its sample projects. Caller commits."""
        user = self._build_demo_user()
        session.add(user)
        session.flush()  # populate user.id for the FK below
        for project in self._build_sample_projects(user.id):
            session.add(project)

    def _build_demo_user(self) -> User:
        return User(
            username=self.DEMO_USERNAME,
            email=self.DEMO_EMAIL,
            password_hash=self._hasher.hash(self.DEMO_PASSWORD),
        )

    def _build_sample_projects(self, owner_id: int) -> Sequence[Project]:
        return [
            Project(
                owner_id=owner_id,
                title="Smart Plant Watering",
                description=(
                    "ESP32-based soil-moisture monitor that turns on a small "
                    "pump when the plant is thirsty and logs readings to a "
                    "cloud dashboard."
                ),
                category=Category.IOT,
                required_skills="MicroPython, soldering, HTTP basics",
                required_tools="ESP32, breadboard, jumper wires",
                required_apis="ThingSpeak",
                required_hardware="Soil-moisture sensor, 5V pump, LiPo cell",
            ),
            Project(
                owner_id=owner_id,
                title="Retrieval-Augmented Chatbot",
                description=(
                    "A small RAG application that answers questions over a "
                    "local PDF corpus using a vector store and a chat model."
                ),
                category=Category.AI,
                required_skills="Python, embeddings, prompt design",
                required_tools="LangChain, Chroma",
                required_apis="OpenAI",
                required_hardware="",
            ),
            Project(
                owner_id=owner_id,
                title="Collaborative Markdown Editor",
                description=(
                    "Browser-based editor with live cursors and presence "
                    "over WebSockets, built on a CRDT for conflict-free "
                    "concurrent edits."
                ),
                category=Category.WEB,
                required_skills="TypeScript, WebSockets, CRDTs",
                required_tools="Yjs, Vite",
                required_apis="",
                required_hardware="",
            ),
            Project(
                owner_id=owner_id,
                title="Habit Tracker",
                description=(
                    "Offline-first mobile app that tracks daily habits, "
                    "keeps streak counts, and sends gentle reminders."
                ),
                category=Category.MOBILE,
                required_skills="Flutter, Dart",
                required_tools="Flutter SDK, Android Studio",
                required_apis="",
                required_hardware="",
            ),
            Project(
                owner_id=owner_id,
                title="DIY Mechanical Keyboard",
                description=(
                    "A hand-soldered 40% split keyboard running QMK "
                    "firmware with per-key RGB."
                ),
                category=Category.HARDWARE,
                required_skills="Soldering, C",
                required_tools="QMK, soldering iron, flux",
                required_apis="",
                required_hardware="Pro Micro, keycaps, switches, plate",
            ),
            Project(
                owner_id=owner_id,
                title="Air-Quality Map",
                description=(
                    "A small network of PM2.5 sensors streaming readings "
                    "to a shared dashboard so you can see pollution "
                    "hotspots in your city."
                ),
                category=Category.IOT,
                required_skills="MicroPython, MQTT, web charts",
                required_tools="ESP32, Mosquitto",
                required_apis="InfluxDB Cloud",
                required_hardware="PMS5003 sensor, OLED display",
            ),
        ]
