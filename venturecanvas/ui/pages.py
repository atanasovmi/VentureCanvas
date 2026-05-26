"""View layer of MVC — NiceGUI pages bound to controller classes.

The :class:`Pages` class holds the four controllers it needs and
registers every ``@ui.page`` route in :meth:`register`. Pages own
layout only; all behaviour is delegated to the controller layer.
Service errors raised by the controllers are caught here and turned
into ``ui.notify`` toasts, so the pages are the single place the UI
speaks to the user.
"""

from __future__ import annotations

from typing import Optional

from nicegui import ui

from ..domain.models import Category, Project
from ..services.errors import (
    AuthError,
    DuplicateError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from .controllers import (
    AuthController,
    CollectionController,
    HomeController,
    ProjectController,
)


class Pages:
    """Registers every NiceGUI route and wires it to the right controller."""

    def __init__(
        self,
        auth_controller: AuthController,
        home_controller: HomeController,
        project_controller: ProjectController,
        collection_controller: CollectionController,
    ) -> None:
        self._auth = auth_controller
        self._home = home_controller
        self._project = project_controller
        self._collection = collection_controller

    # ------------------------------------------------------------------ register

    def register(self) -> None:
        """Attach every ``@ui.page`` to a bound method on this instance."""
        ui.page("/")(self._home_page)
        ui.page("/login")(self._login_page)
        ui.page("/register")(self._register_page)
        ui.page("/project/new")(self._project_new_page)
        ui.page("/project/{project_id}")(self._project_detail_page)
        ui.page("/project/{project_id}/edit")(self._project_edit_page)
        ui.page("/my-projects")(self._my_projects_page)
        ui.page("/collection")(self._collection_page)

    # ------------------------------------------------------------------ layout

    def _header(self) -> None:
        """Shared top-bar; every page calls this once at the start."""
        with ui.header().classes("items-center justify-between"):
            with ui.row().classes("items-center gap-4"):
                ui.link("🚀 VentureCanvas", "/").classes(
                    "text-lg font-bold no-underline text-white"
                )
                ui.link("Home", "/").classes("no-underline text-white")
                if self._auth.is_authenticated:
                    ui.link("My Projects", "/my-projects").classes(
                        "no-underline text-white"
                    )
                    ui.link("Collection", "/collection").classes(
                        "no-underline text-white"
                    )
                    ui.link("New project", "/project/new").classes(
                        "no-underline text-white"
                    )
            with ui.row().classes("items-center gap-3"):
                if self._auth.is_authenticated:
                    ui.label(f"@{self._auth.current_user().username}").classes(
                        "text-white"
                    )
                    ui.button("Logout", on_click=self._handle_logout).props(
                        "flat color=white"
                    )
                else:
                    ui.link("Login", "/login").classes("no-underline text-white")
                    ui.link("Register", "/register").classes(
                        "no-underline text-white"
                    )

    def _handle_logout(self) -> None:
        self._auth.logout()
        ui.notify("Logged out.", type="info")
        ui.navigate.to("/")

    # ------------------------------------------------------------------ home

    def _home_page(self) -> None:
        self._header()
        selected: dict[str, Optional[Category]] = {"category": None}
        with ui.column().classes("w-full p-6 gap-4 items-start"):
            ui.label("Discover innovation projects").classes("text-2xl font-bold")


            with ui.row().classes("gap-2 items-center"):
                def select(cat: Optional[Category]) -> None:
                    selected["category"] = cat
                    refresh()

                ui.button("All", on_click=lambda: select(None)).props("outline")
                for cat in self._home.available_categories():
                    ui.button(
                        cat.value, on_click=lambda c=cat: select(c)
                    ).props("outline")

            grid = ui.column().classes("w-full gap-3")

            def refresh() -> None:
                grid.clear()
                projects = self._home.list(category=selected["category"])
                with grid:
                    if not projects:
                        ui.label("No projects yet.").classes("text-grey-7")
                        return
                    with ui.row().classes("w-full gap-4 flex-wrap"):
                        for project in projects:
                            self._render_project_card(project)

            refresh()

    def _render_project_card(self, project: Project) -> None:
        with ui.card().classes("w-80"):
            ui.label(project.title).classes("text-lg font-bold")
            ui.label(project.category.value).classes("text-caption text-primary")
            ui.label(project.description[:140] + ("…" if len(project.description) > 140 else "")).classes(
                "text-sm"
            )
            ui.button(
                "View",
                on_click=lambda pid=project.id: ui.navigate.to(f"/project/{pid}"),
            ).props("flat color=primary")

    # ------------------------------------------------------------------ login / register

    def _login_page(self) -> None:
        self._header()
        with ui.card().classes("max-w-md mx-auto mt-12 p-6"):
            ui.label("Login").classes("text-xl font-bold mb-2")
            email = ui.input("Email").classes("w-full")
            password = ui.input("Password", password=True, password_toggle_button=True).classes("w-full")

            def submit() -> None:
                try:
                    self._auth.login(email=email.value, password=password.value)
                except AuthError as exc:
                    ui.notify(str(exc), type="negative")
                    return
                ui.notify("Logged in.", type="positive")
                ui.navigate.to("/")

            ui.button("Log in", on_click=submit).props("color=primary")
            ui.link("Need an account? Register", "/register").classes("block mt-3")

    def _register_page(self) -> None:
        self._header()
        with ui.card().classes("max-w-md mx-auto mt-12 p-6"):
            ui.label("Create account").classes("text-xl font-bold mb-2")
            username = ui.input("Username").classes("w-full")
            email = ui.input("Email").classes("w-full")
            password = ui.input("Password", password=True, password_toggle_button=True).classes("w-full")

            def submit() -> None:
                try:
                    self._auth.register(
                        username=username.value,
                        email=email.value,
                        password=password.value,
                    )
                except (ValidationError, DuplicateError) as exc:
                    ui.notify(str(exc), type="warning")
                    return
                ui.notify("Account created. Please log in.", type="positive")
                ui.navigate.to("/login")

            ui.button("Register", on_click=submit).props("color=primary")
            ui.link("Already have an account? Log in", "/login").classes("block mt-3")

    # ------------------------------------------------------------------ project detail / new / edit

    def _project_detail_page(self, project_id: int) -> None:
        self._header()
        try:
            project = self._project.get(project_id)
        except NotFoundError:
            with ui.column().classes("p-6"):
                ui.label("Project not found.").classes("text-xl")
                ui.link("← Back to home", "/")
            return

        with ui.column().classes("max-w-3xl mx-auto p-6 gap-3"):
            with ui.row().classes("items-center justify-between w-full"):
                ui.label(project.title).classes("text-2xl font-bold")
                ui.label(project.category.value).classes("text-primary")

            ui.label(project.description).classes("whitespace-pre-wrap")

            self._render_requirement("Skills", project.required_skills)
            self._render_requirement("Tools", project.required_tools)
            self._render_requirement("APIs", project.required_apis)
            self._render_requirement("Hardware", project.required_hardware)

            with ui.row().classes("gap-2 mt-4"):
                if self._auth.is_authenticated:
                    ui.button(
                        "Add to collection",
                        on_click=lambda: self._handle_add_to_collection(project.id),
                    ).props("color=primary")
                if self._project.is_owner(project):
                    ui.button(
                        "Edit",
                        on_click=lambda: ui.navigate.to(f"/project/{project.id}/edit"),
                    ).props("outline color=primary")
                    ui.button(
                        "Delete",
                        on_click=lambda: self._handle_delete_project(project.id),
                    ).props("outline color=negative")

    def _render_requirement(self, label: str, raw_value: str) -> None:
        if not raw_value:
            return
        tokens = [t.strip() for t in raw_value.split(",") if t.strip()]
        if not tokens:
            return
        with ui.row().classes("items-center gap-2"):
            ui.label(f"{label}:").classes("font-semibold")
            for tok in tokens:
                ui.chip(tok, color="primary").props("outline")

    def _handle_add_to_collection(self, project_id: int) -> None:
        try:
            self._collection.add(project_id)
        except (ForbiddenError, NotFoundError) as exc:
            ui.notify(str(exc), type="warning")
            return
        except DuplicateError as exc:
            ui.notify(str(exc), type="info")
            return
        ui.notify("Added to collection.", type="positive")

    def _handle_delete_project(self, project_id: int) -> None:
        try:
            self._project.delete(project_id)
        except (ForbiddenError, NotFoundError) as exc:
            ui.notify(str(exc), type="warning")
            return
        ui.notify("Project deleted.", type="positive")
        ui.navigate.to("/")

    def _project_new_page(self) -> None:
        self._header()
        if not self._guard_authenticated():
            return
        with ui.card().classes("w-full max-w-4xl mx-auto mt-8 p-8"):
            ui.label("New project").classes("text-2xl font-bold mb-4")

            with ui.row().classes("w-full gap-4 items-start"):
                title = ui.input("Title").classes("flex-grow")
                category = ui.select(
                    {c.value: c.value for c in self._home.available_categories()},
                    label="Category",
                ).classes("w-48")

            description = ui.textarea("Description").props(
                "rows=4 autogrow"
            ).classes("w-full mt-2")

            ui.label("Requirements").classes(
                "text-sm font-semibold mt-4 text-grey-7"
            )
            with ui.grid(columns=2).classes("w-full gap-x-4 gap-y-0"):
                skills = ui.input(
                    "Skills", placeholder="e.g. Python, MQTT"
                ).classes("w-full")
                tools = ui.input(
                    "Tools", placeholder="e.g. ESP32, Mosquitto"
                ).classes("w-full")
                apis = ui.input(
                    "APIs", placeholder="e.g. OpenAI"
                ).classes("w-full")
                hardware = ui.input(
                    "Hardware", placeholder="e.g. Sensor, OLED"
                ).classes("w-full")

            def submit() -> None:
                if not category.value:
                    ui.notify("Please pick a category.", type="warning")
                    return
                try:
                    project = self._project.create(
                        title=title.value,
                        description=description.value,
                        category=Category(category.value),
                        required_skills=skills.value or "",
                        required_tools=tools.value or "",
                        required_apis=apis.value or "",
                        required_hardware=hardware.value or "",
                    )
                except (ValidationError, ForbiddenError) as exc:
                    ui.notify(str(exc), type="warning")
                    return
                ui.notify("Project created.", type="positive")
                ui.navigate.to(f"/project/{project.id}")

            with ui.row().classes("w-full justify-end gap-2 mt-6"):
                ui.button("Create", on_click=submit).props("color=primary")

    def _project_edit_page(self, project_id: int) -> None:
        self._header()
        if not self._guard_authenticated():
            return
        try:
            project = self._project.get(project_id)
        except NotFoundError:
            ui.label("Project not found.").classes("text-xl p-6")
            return
        if not self._project.is_owner(project):
            ui.notify("You can only edit your own projects.", type="warning")
            ui.navigate.to(f"/project/{project_id}")
            return

        with ui.card().classes("w-full max-w-4xl mx-auto mt-8 p-8"):
            ui.label(f"Edit: {project.title}").classes("text-2xl font-bold mb-4")

            with ui.row().classes("w-full gap-4 items-start"):
                title = ui.input("Title", value=project.title).classes("flex-grow")
                category = ui.select(
                    {c.value: c.value for c in self._home.available_categories()},
                    label="Category",
                    value=project.category.value,
                ).classes("w-48")

            description = ui.textarea(
                "Description", value=project.description
            ).props("rows=4 autogrow").classes("w-full mt-2")

            ui.label("Requirements").classes(
                "text-sm font-semibold mt-4 text-grey-7"
            )
            with ui.grid(columns=2).classes("w-full gap-x-4 gap-y-0"):
                skills = ui.input(
                    "Skills",
                    value=project.required_skills,
                    placeholder="e.g. Python, MQTT",
                ).classes("w-full")
                tools = ui.input(
                    "Tools",
                    value=project.required_tools,
                    placeholder="e.g. ESP32, Mosquitto",
                ).classes("w-full")
                apis = ui.input(
                    "APIs",
                    value=project.required_apis,
                    placeholder="e.g. OpenAI",
                ).classes("w-full")
                hardware = ui.input(
                    "Hardware",
                    value=project.required_hardware,
                    placeholder="e.g. Sensor, OLED",
                ).classes("w-full")

            def submit() -> None:
                try:
                    self._project.update(
                        project_id=project.id,
                        title=title.value,
                        description=description.value,
                        category=Category(category.value),
                        required_skills=skills.value or "",
                        required_tools=tools.value or "",
                        required_apis=apis.value or "",
                        required_hardware=hardware.value or "",
                    )
                except (ValidationError, ForbiddenError, NotFoundError) as exc:
                    ui.notify(str(exc), type="warning")
                    return
                ui.notify("Project updated.", type="positive")
                ui.navigate.to(f"/project/{project.id}")

            with ui.row().classes("w-full justify-end gap-2 mt-6"):
                ui.button("Save", on_click=submit).props("color=primary")

    # ------------------------------------------------------------------ my projects

    def _my_projects_page(self) -> None:
        self._header()
        if not self._guard_authenticated():
            return
        projects = self._project.list_mine()
        with ui.column().classes("w-full p-6 gap-4 items-start"):
            ui.label("My projects").classes("text-2xl font-bold")
            if not projects:
                ui.label("You haven't created any projects yet.").classes(
                    "text-grey-7"
                )
                ui.link("Create your first project", "/project/new").classes(
                    "block mt-2"
                )
                return
            with ui.row().classes("w-full gap-4 flex-wrap"):
                for project in projects:
                    self._render_project_card(project)

    # ------------------------------------------------------------------ collection

    def _collection_page(self) -> None:
        self._header()
        if not self._guard_authenticated():
            return

        projects, summary = self._collection.view()
        with ui.row().classes("w-full p-6 gap-6 items-start"):
            with ui.column().classes("flex-grow gap-3"):
                ui.label("My collection").classes("text-2xl font-bold")
                if not projects:
                    ui.label(
                        "Your collection is empty. Add projects from their detail page."
                    ).classes("text-grey-7")
                else:
                    for project in projects:
                        with ui.card().classes("w-full"):
                            with ui.row().classes(
                                "items-center justify-between w-full"
                            ):
                                ui.label(project.title).classes("font-bold")
                                ui.label(project.category.value).classes(
                                    "text-primary"
                                )
                            ui.label(project.description[:180]).classes("text-sm")
                            with ui.row().classes("gap-2"):
                                ui.button(
                                    "Open",
                                    on_click=lambda pid=project.id: ui.navigate.to(
                                        f"/project/{pid}"
                                    ),
                                ).props("flat color=primary")
                                ui.button(
                                    "Remove",
                                    on_click=lambda pid=project.id: self._handle_remove_from_collection(pid),
                                ).props("flat color=negative")

            with ui.card().classes("w-80"):
                ui.label("Resource summary").classes("text-lg font-bold mb-2")
                self._render_summary_section("Skills", summary["skills"])
                self._render_summary_section("Tools", summary["tools"])
                self._render_summary_section("APIs", summary["apis"])
                self._render_summary_section("Hardware", summary["hardware"])

    def _render_summary_section(self, label: str, items: list[str]) -> None:
        if not items:
            return
        ui.label(label).classes("text-sm font-semibold mt-2")
        with ui.row().classes("flex-wrap gap-1"):
            for item in items:
                ui.chip(item, color="primary").props("outline")

    def _handle_remove_from_collection(self, project_id: int) -> None:
        try:
            self._collection.remove(project_id)
        except (NotFoundError, ForbiddenError) as exc:
            ui.notify(str(exc), type="warning")
            return
        ui.notify("Removed from collection.", type="positive")
        ui.navigate.to("/collection")

    # ------------------------------------------------------------------ guards

    def _guard_authenticated(self) -> bool:
        """Redirect to /login if not authenticated. Returns True if allowed through."""
        if self._auth.is_authenticated:
            return True
        ui.notify("Please log in first.", type="info")
        ui.navigate.to("/login")
        return False
