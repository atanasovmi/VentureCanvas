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

# ============================================================================
# Landing-page presentation data, icons & client script.
# Pure layout assets — no business logic. Kept at module level so the page
# helper methods stay short and declarative.
# ============================================================================

GITHUB_REPO = "https://github.com/atanasovmi/VentureCanvas"

# Lucide-style line icons (24x24, stroke=currentColor). Rendered as trusted,
# hand-authored SVG via ``ui.html(sanitize=False)`` — never emojis.
_ICON_PATHS: dict[str, str] = {
    "arrow-right": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "arrow-down": '<path d="M12 5v14"/><path d="m19 12-7 7-7-7"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    "menu": '<path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h16"/>',
    "user-plus": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>'
                 '<circle cx="9" cy="7" r="4"/><path d="M19 8v6"/><path d="M22 11h-6"/>',
    "lightbulb": '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 '
                 '1.5 3.5.7.7 1.3 1.6 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/>',
    "compass": '<circle cx="12" cy="12" r="10"/>'
               '<path d="m16.24 7.76-1.8 5.41a2 2 0 0 1-1.27 1.27l-5.41 1.8 1.8-5.41a2 2 0 0 1 1.27-1.27z"/>',
    "bookmark": '<path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>',
    "bookmark-plus": '<path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>'
                     '<path d="M9 10h6"/><path d="M12 7v6"/>',
    "settings-2": '<path d="M20 7h-9"/><path d="M14 17H5"/>'
                  '<circle cx="17" cy="17" r="3"/><circle cx="7" cy="7" r="3"/>',
    "layers": '<path d="M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 '
              '1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z"/>'
              '<path d="M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12"/>'
              '<path d="M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17"/>',
    "circle-check": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "list-checks": '<path d="m3 17 2 2 4-4"/><path d="m3 7 2 2 4-4"/>'
                   '<path d="M13 6h8"/><path d="M13 12h8"/><path d="M13 18h8"/>',
    "circle-plus": '<circle cx="12" cy="12" r="10"/><path d="M8 12h8"/><path d="M12 8v8"/>',
    "quote": '<path d="M10 11H6a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v6c0 2-1 3-3 4"/>'
             '<path d="M19 11h-4a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v6c0 2-1 3-3 4"/>',
    "github": '<path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15'
              '.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5'
              'A5.4 5.4 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 '
              '1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/>',
    "cpu": '<rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/>'
           '<path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/>'
           '<path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/>',
    "sparkles": '<path d="M9.94 14.06A2 2 0 0 0 8.5 12.6l-5.2-1.4a.5.5 0 0 1 0-.96l5.2-1.4A2 2 0 0 0 '
                '9.94 7.4l1.4-5.2a.5.5 0 0 1 .96 0l1.4 5.2a2 2 0 0 0 1.44 1.44l5.2 1.4a.5.5 0 0 1 0 '
                '.96l-5.2 1.4a2 2 0 0 0-1.44 1.44l-1.4 5.2a.5.5 0 0 1-.96 0z"/>'
                '<path d="M20 3v4"/><path d="M22 5h-4"/><path d="M4 17v2"/><path d="M5 18H3"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/>'
             '<path d="M2 12h20"/>',
    "smartphone": '<rect width="14" height="20" x="5" y="2" rx="2"/><path d="M12 18h.01"/>',
    "circuit-board": '<rect width="18" height="18" x="3" y="3" rx="2"/>'
                     '<path d="M11 9h4a2 2 0 0 0 2-2V3"/><circle cx="9" cy="9" r="2"/>'
                     '<path d="M7 21v-4a2 2 0 0 1 2-2h4"/><circle cx="15" cy="15" r="2"/>',
}


# The data above is module-level reference data (immutable lookup tables and
# copy). The helpers that *render* it — inline SVG, headings, the logo glyph —
# live as methods on the Pages class instead, per Plan.md §0.1: behaviour
# belongs to the class that owns it, not to loose module-level functions.

_CATEGORIES = [
    ("IoT", "cpu", "Sensors & connected devices"),
    ("AI", "sparkles", "Models, agents & RAG"),
    ("Web", "globe", "Apps that live in the browser"),
    ("Mobile", "smartphone", "iOS & Android builds"),
    ("Hardware", "circuit-board", "PCBs, robotics & physical builds"),
]
_CATEGORY_ICON = {name: icon for name, icon, _desc in _CATEGORIES}

_STEPS = [
    ("1", "circle-plus", "Create",
     "Post your idea with the skills, tools, APIs and hardware it needs — "
     "or browse the gallery first for inspiration."),
    ("2", "bookmark-plus", "Discover & collect",
     "Filter the community gallery by category and save the projects you'd love to build."),
    ("3", "list-checks", "Plan resources",
     "Open your collection and read one unified list of everything you'll need to build it all."),
]

# Real seeded projects (venturecanvas/data_access/seed.py) — used verbatim so the
# Resource-Summary demo is authentic and self-consistent.
_SPOTLIGHT_BEFORE = [
    ("Smart Plant Watering", "IoT",
     [("Skills", "MicroPython, soldering"), ("Tools", "ESP32"),
      ("APIs", "ThingSpeak"), ("Hardware", "Soil sensor, 5V pump")]),
    ("RAG Chatbot", "AI",
     [("Skills", "Python, embeddings"), ("Tools", "LangChain, Chroma"),
      ("APIs", "OpenAI")]),
    ("DIY Mechanical Keyboard", "Hardware",
     [("Skills", "Soldering, C"), ("Tools", "QMK, soldering iron"),
      ("Hardware", "Pro Micro, switches")]),
]
_SPOTLIGHT_AFTER = [
    ("Skills", ["C", "embeddings", "MicroPython", "Python", "soldering"]),
    ("Tools", ["Chroma", "ESP32", "LangChain", "QMK", "soldering iron"]),
    ("APIs", ["OpenAI", "ThingSpeak"]),
    ("Hardware", ["5V pump", "Pro Micro", "Soil sensor", "switches"]),
]

# Client-side enhancement: scroll-reveal, count-up stats, sticky-nav state.
# Wrapped so a slow/absent run never leaves content hidden (see .vc-js gate).
_LANDING_JS = """
(function () {
  try {
    var reduce = window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var root = document.documentElement;

    // Reveal-on-scroll (only enable the hidden state when we can animate).
    var reveals = document.querySelectorAll('.vc-reveal');
    if (!reduce && 'IntersectionObserver' in window) {
      root.classList.add('vc-js');
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
        });
      }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
      reveals.forEach(function (el) { io.observe(el); });
    }

    // Count-up stats (text already holds the final value as a fallback).
    var counters = document.querySelectorAll('[data-count]');
    function runCount(el) {
      var target = parseFloat(el.getAttribute('data-count')) || 0;
      var dur = 1200, start = null;
      function step(ts) {
        if (!start) start = ts;
        var p = Math.min((ts - start) / dur, 1);
        el.textContent = Math.floor(p * target).toString();
        if (p < 1) requestAnimationFrame(step); else el.textContent = target.toString();
      }
      requestAnimationFrame(step);
    }
    if (!reduce && 'IntersectionObserver' in window) {
      var cio = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { runCount(e.target); cio.unobserve(e.target); }
        });
      }, { threshold: 0.6 });
      counters.forEach(function (el) { cio.observe(el); });
    }

    // Sticky-nav opacity state.
    var nav = document.getElementById('vc-nav');
    if (nav) {
      var onScroll = function () {
        nav.classList.toggle('is-scrolled', window.scrollY > 80);
      };
      window.addEventListener('scroll', onScroll, { passive: true });
      onScroll();
    }
  } catch (err) { /* never block the page on enhancement */ }
})();
"""


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

    # ------------------------------------------------------- presentation helpers
    # Small, stateless builders for the trusted inline markup the pages render.
    # They are methods (not module functions) so all rendering behaviour lives
    # on the View class — see the note by the icon tables above.

    def _icon_svg(self, name: str, size: int = 24, stroke: float = 2) -> str:
        """Return an inline SVG string for ``name`` (decorative; aria-hidden)."""
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
            f'width="{size}" height="{size}" fill="none" stroke="currentColor" '
            f'stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round" '
            f'aria-hidden="true">{_ICON_PATHS[name]}</svg>'
        )

    def _ico(self, name: str, classes: str = "", size: int = 24, stroke: float = 2):
        """Inline-render a trusted SVG icon, colourable via Tailwind text classes."""
        return ui.html(
            self._icon_svg(name, size, stroke), sanitize=False, tag="span"
        ).classes(f"inline-flex items-center justify-center {classes}")

    def _heading(self, level: int, inner_html: str, classes: str = ""):
        """Render a real heading element (semantic h1..h4) with trusted markup."""
        return ui.html(inner_html, sanitize=False, tag=f"h{level}").classes(classes)

    def _logo_glyph(self, height_px: int, extra_style: str = ""):
        """The bold 'VC' glyph as a crisp <img> at a fixed height."""
        return ui.html(
            f'<img src="/static/logo_glyph.png" alt="VentureCanvas" '
            f'style="height:{height_px}px;width:auto;display:block;{extra_style}">',
            sanitize=False,
            tag="span",
        ).classes("inline-flex items-center")

    # ------------------------------------------------------------------ register

    def register(self) -> None:
        """Attach every ``@ui.page`` to a bound method on this instance."""
        # Each line maps a URL to a page method. `{project_id}` is a path
        # parameter NiceGUI passes straight into the matching method argument.
        ui.page("/")(self._landing_page)
        ui.page("/home")(self._home_page)  
        ui.page("/login")(self._login_page)
        ui.page("/register")(self._register_page)
        ui.page("/project/new")(self._project_new_page)
        ui.page("/project/{project_id}")(self._project_detail_page)
        ui.page("/project/{project_id}/edit")(self._project_edit_page)
        ui.page("/my-projects")(self._my_projects_page)
        ui.page("/collection")(self._collection_page)

    # ------------------------------------------------------------------ layout

    def _apply_brand(self) -> None:
        """Theme Quasar's colour roles to the VentureCanvas terracotta brand
        so every ``color=primary`` button/chip/link matches the landing page."""
        ui.colors(
            primary="#C2410C", secondary="#0A0A0A", accent="#EA580C",
            positive="#16A34A", negative="#DC2626", info="#0A0A0A", warning="#D97706",
        )

    def _header(self) -> None:
        """Shared top-bar; every page calls this once at the start.

        Restyled to a clean light bar carrying the official VentureCanvas
        logo so the brand stays consistent across every page.
        """
        self._apply_brand()
        with ui.header().classes("vc-appbar items-center justify-between px-4 py-2"):
            with ui.row().classes("items-center gap-5"):
                with ui.link(target="/home").classes(
                    "flex items-center gap-2 no-underline"
                ):
                    self._logo_glyph(26)
                    ui.label("VentureCanvas").classes("vc-wordmark text-base")
                ui.link("Home", "/home").classes("vc-appbar-link")
                if self._auth.is_authenticated:
                    ui.link("My Projects", "/my-projects").classes("vc-appbar-link")
                    ui.link("Collection", "/collection").classes("vc-appbar-link")
                    ui.link("New project", "/project/new").classes("vc-appbar-link")
            with ui.row().classes("items-center gap-3"):
                if self._auth.is_authenticated:
                    ui.label(f"@{self._auth.current_user().username}").classes(
                        "text-sm text-[#57534E]"
                    )
                    ui.button("Logout", on_click=self._handle_logout).props(
                        "flat no-caps"
                    ).style("color:var(--vc-indigo-700);font-weight:600")
                else:
                    ui.link("Login", "/login").classes("vc-appbar-link")
                    ui.link("Register", "/register").classes(
                        "vc-btn vc-btn-primary vc-btn-sm no-underline"
                    )

    def _handle_logout(self) -> None:
        self._auth.logout()
        ui.notify("Logged out.", type="info")
        ui.navigate.to("/")



    # ------------------------------------------------------------------ landing page

    def _landing_page(self) -> None:
        """Marketing landing page — all-light premium, bold & promising."""
        self._apply_brand()
        # Full-bleed: strip NiceGUI's default content padding/gap for "/" only.
        # ui.query is per-client, so other pages keep their normal padded layout.
        ui.query(".nicegui-content").style("padding:0; gap:0; max-width:100%;")
        ui.query(".q-page").style("padding:0;")
        ui.query("body").classes(add="vc-landing")

        with ui.element("div").classes("vc-landing w-full"):
            self._landing_nav()
            with ui.element("main").classes("w-full"):
                self._landing_hero()
                self._landing_categories()
                self._landing_problem_solution()
                self._landing_features()
                self._landing_how()
                self._landing_resource_spotlight()
                self._landing_social_proof()
                self._landing_cta()
            self._landing_footer()

        # Client-side enhancement (reveal/counters/sticky-nav) once the DOM exists.
        ui.timer(0.2, lambda: ui.run_javascript(_LANDING_JS), once=True)

    # ----- landing: navbar ---------------------------------------------------

    def _landing_nav(self) -> None:
        guest = not self._auth.is_authenticated
        with ui.element("nav").classes(
            "fixed top-4 left-3 right-3 md:left-4 md:right-4 z-50"
        ):
            with ui.element("div").classes(
                "vc-nav mx-auto max-w-7xl flex items-center justify-between gap-4 "
                "px-4 md:px-5 h-16 rounded-2xl"
            ) as bar:
                bar.props["id"] = "vc-nav"
                with ui.link(target="/").classes(
                    "flex items-center gap-2.5 no-underline shrink-0"
                ):
                    self._logo_glyph(28)
                    ui.label("VentureCanvas").classes("vc-wordmark text-lg")
                with ui.element("div").classes("hidden md:flex items-center gap-8"):
                    ui.link("Features", "#features").classes("vc-nav-link")
                    ui.link("Categories", "#categories").classes("vc-nav-link")
                    ui.link("How it works", "#how").classes("vc-nav-link")
                with ui.element("div").classes("flex items-center gap-2 md:gap-3"):
                    if guest:
                        ui.link("Log in", "/login").classes(
                            "vc-nav-link hidden sm:inline-flex"
                        )
                        with ui.link(target="/register").classes(
                            "vc-btn vc-btn-primary vc-btn-sm no-underline"
                        ):
                            ui.label("Get started")
                            self._ico("arrow-right", "", 16)
                    else:
                        with ui.element("div").classes(
                            "hidden sm:flex items-center gap-2 mr-1"
                        ):
                            ui.html('<span class="vc-live-dot"></span>', sanitize=False)
                            ui.label(
                                f"@{self._auth.current_user().username}"
                            ).classes("text-sm text-[#57534E]")
                        ui.link("Dashboard", "/home").classes(
                            "vc-btn vc-btn-primary vc-btn-sm no-underline"
                        )
                        ui.button("Log out", on_click=self._handle_logout).props(
                            "flat no-caps"
                        ).style("color:var(--vc-body);font-weight:600")
                    self._landing_mobile_menu(guest)

    def _landing_mobile_menu(self, guest: bool) -> None:
        with ui.element("div").classes("md:hidden flex items-center"):
            with ui.button(icon="menu").props(
                'flat round dense aria-label="Open menu"'
            ).style("color:var(--vc-ink)"):
                with ui.menu().classes("rounded-xl"):
                    def go(sel: str) -> None:
                        ui.run_javascript(
                            f"document.querySelector('{sel}')"
                            f".scrollIntoView({{behavior:'smooth'}})"
                        )

                    ui.menu_item("Features", lambda: go("#features"))
                    ui.menu_item("Categories", lambda: go("#categories"))
                    ui.menu_item("How it works", lambda: go("#how"))
                    ui.separator()
                    if guest:
                        ui.menu_item("Log in", lambda: ui.navigate.to("/login"))
                        ui.menu_item("Get started", lambda: ui.navigate.to("/register"))
                    else:
                        ui.menu_item("Dashboard", lambda: ui.navigate.to("/home"))
                        ui.menu_item("My collection", lambda: ui.navigate.to("/collection"))
                        ui.menu_item("Log out", self._handle_logout)

    # ----- landing: hero -----------------------------------------------------

    def _landing_hero(self) -> None:
        guest = not self._auth.is_authenticated
        with ui.element("section").classes("vc-hero w-full"):
            ui.html('<div class="vc-hero-glow vc-deco"></div>', sanitize=False)
            ui.html('<div class="vc-grid-tex vc-deco"></div>', sanitize=False)
            with ui.element("div").classes(
                "relative z-10 mx-auto max-w-7xl px-6 md:px-8 pt-36 pb-20 lg:pt-44 lg:pb-28"
            ):
                with ui.element("div").classes(
                    "grid lg:grid-cols-[1.05fr_0.95fr] gap-12 lg:gap-16 items-center"
                ):
                    with ui.element("div").classes(
                        "flex flex-col items-start gap-6 max-w-xl"
                    ):
                        with ui.element("div").classes("vc-reveal vc-chip vc-chip-live"):
                            ui.html('<span class="vc-live-dot"></span>', sanitize=False)
                            ui.label("A growing community of makers")
                        self._heading(
                            1,
                            "Share ideas. Build together.<br>"
                            '<span class="vc-grad-text">Create impact.</span>',
                            "vc-reveal vc-d1 font-bold leading-[1.05] "
                            "text-[clamp(2.6rem,6vw,4.6rem)]",
                        )
                        ui.label(
                            "VentureCanvas is where makers, students and innovators "
                            "publish project ideas, discover what others are building, "
                            "and curate a shortlist — then instantly see every skill, "
                            "tool, API and component they'd need to build them all."
                        ).classes(
                            "vc-reveal vc-d2 text-lg md:text-xl text-[#57534E] leading-relaxed"
                        )
                        with ui.element("div").classes(
                            "vc-reveal vc-d3 flex flex-col sm:flex-row gap-3 pt-1"
                        ):
                            if guest:
                                with ui.link(target="/home").classes(
                                    "vc-btn vc-btn-primary vc-btn-lg no-underline"
                                ):
                                    ui.label("Discover projects")
                                    self._ico("arrow-right", "", 18)
                                with ui.link(target="/register").classes(
                                    "vc-btn vc-btn-secondary vc-btn-lg no-underline"
                                ):
                                    self._ico("user-plus", "", 18)
                                    ui.label("Join free")
                            else:
                                with ui.link(target="/home").classes(
                                    "vc-btn vc-btn-primary vc-btn-lg no-underline"
                                ):
                                    ui.label("Go to dashboard")
                                    self._ico("arrow-right", "", 18)
                                with ui.link(target="/collection").classes(
                                    "vc-btn vc-btn-secondary vc-btn-lg no-underline"
                                ):
                                    ui.label("My collection")
                        with ui.element("div").classes(
                            "vc-reveal vc-d4 flex flex-wrap gap-8 pt-7 mt-1 "
                            "border-t border-[#E7E5E4] w-full"
                        ):
                            self._hero_stat("80", "+", "project ideas")
                            self._hero_stat("5", "", "categories")
                            self._hero_stat("4", "", "resource types unified")
                    self._hero_preview()

    def _hero_stat(self, value: str, suffix: str, label: str) -> None:
        with ui.element("div").classes("flex flex-col gap-1"):
            ui.html(
                '<div class="flex items-baseline">'
                f'<span class="vc-stat-num text-3xl md:text-4xl" data-count="{value}">{value}</span>'
                f'<span class="vc-stat-num text-3xl md:text-4xl">{suffix}</span>'
                "</div>",
                sanitize=False,
            )
            ui.label(label).classes("text-sm text-[#57534E]")

    def _hero_preview(self) -> None:
        with ui.element("div").classes(
            "vc-reveal vc-d2 relative w-full max-w-md mx-auto lg:ml-auto"
        ):
            ui.html(
                '<div class="vc-deco" style="position:absolute;inset:-1.4rem;'
                "border-radius:34px;background:var(--vc-grad-soft);"
                'filter:blur(48px);opacity:.22"></div>',
                sanitize=False,
            )
            with ui.element("div").classes("vc-panel vc-float relative p-5"):
                with ui.element("div").classes("flex items-center justify-between mb-4"):
                    with ui.element("div").classes("flex items-center gap-2.5"):
                        with ui.element("div").classes("vc-ico").style(
                            "width:38px;height:38px"
                        ):
                            self._ico("bookmark", "", 20)
                        with ui.element("div").classes("flex flex-col"):
                            ui.label("My collection").classes(
                                "vc-head text-sm font-semibold leading-tight"
                            )
                            ui.label("Smart-home weekend builds").classes(
                                "text-xs text-[#A8A29E]"
                            )
                    with ui.element("div").classes("vc-chip"):
                        ui.html('<span class="vc-live-dot"></span>', sanitize=False)
                        ui.label("3 saved")
                for title, cat, chips in [
                    ("Smart Plant Watering", "IoT", ["ESP32", "Soil sensor"]),
                    ("RAG Chatbot", "AI", ["OpenAI", "LangChain"]),
                    ("DIY Mechanical Keyboard", "Hardware", ["QMK", "Switches"]),
                ]:
                    with ui.element("div").classes(
                        "flex items-center justify-between gap-2 py-2.5 "
                        "border-b border-[#E7E5E4]"
                    ):
                        with ui.element("div").classes("flex flex-col gap-0.5 min-w-0"):
                            ui.label(title).classes(
                                "text-sm font-semibold text-[#0A0A0A] truncate"
                            )
                            ui.label(cat).classes("text-xs text-[#C2410C] font-medium")
                        with ui.element("div").classes("flex gap-1 shrink-0"):
                            for chip in chips:
                                with ui.element("span").classes("vc-chip"):
                                    ui.label(chip)
                with ui.element("div").classes("flex justify-center py-3"):
                    self._ico("chevron-down", "text-[#A8A29E]", 22)
                with ui.element("div").classes("vc-panel-dark p-4"):
                    with ui.element("div").classes("flex items-center gap-2 mb-3"):
                        with ui.element("div").classes("vc-ico vc-ico-light").style(
                            "width:30px;height:30px;border-radius:9px"
                        ):
                            self._ico("layers", "", 16)
                        ui.label("Resource Summary").classes(
                            "vc-head text-white text-sm font-semibold"
                        )
                    with ui.element("div").classes("grid grid-cols-2 gap-x-4 gap-y-3"):
                        for lbl, items in [
                            ("Skills", "Python · soldering"),
                            ("Tools", "ESP32 · QMK"),
                            ("APIs", "OpenAI · ThingSpeak"),
                            ("Hardware", "Sensor · Switches"),
                        ]:
                            with ui.element("div").classes("flex flex-col gap-1"):
                                ui.label(lbl).classes(
                                    "text-[10px] uppercase tracking-wider "
                                    "text-[#A8A29E] font-semibold"
                                )
                                ui.label(items).classes("text-xs text-[#E7E5E4]")

    # ----- landing: categories ----------------------------------------------

    def _landing_categories(self) -> None:
        with ui.element("section").classes("w-full bg-white"):
            ui.html('<span id="categories" class="vc-anchor"></span>', sanitize=False)
            with ui.element("div").classes(
                "mx-auto max-w-7xl px-6 md:px-8 py-16 md:py-24"
            ):
                with ui.element("div").classes(
                    "vc-reveal flex flex-col items-center text-center gap-3 mb-10"
                ):
                    ui.label("Explore by category").classes("vc-eyebrow")
                    self._heading(2, "Five tracks. One community.",
                             "text-3xl md:text-4xl font-bold")
                    ui.label(
                        "From a weekend Arduino build to a production RAG app — "
                        "there's a place for it."
                    ).classes("text-[#57534E] max-w-xl")
                with ui.element("div").classes(
                    "grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4"
                ):
                    for i, (name, icon, desc) in enumerate(_CATEGORIES):
                        with ui.link(target="/home").classes(
                            f"vc-cat-card vc-reveal vc-d{min(i + 1, 5)} no-underline"
                        ):
                            with ui.element("div").classes("vc-ico"):
                                self._ico(icon, "", 22)
                            ui.label(name).classes("vc-head text-lg font-semibold")
                            ui.label(desc).classes("text-sm text-[#57534E]")

    # ----- landing: problem / solution --------------------------------------

    def _landing_problem_solution(self) -> None:
        with ui.element("section").classes("w-full bg-[#FAFAF9]"):
            with ui.element("div").classes(
                "mx-auto max-w-6xl px-6 md:px-8 py-20 md:py-28 "
                "grid lg:grid-cols-2 gap-12 lg:gap-16 items-center"
            ):
                with ui.element("div").classes("vc-reveal flex flex-col gap-5"):
                    ui.label("The problem").classes("vc-eyebrow")
                    self._heading(2, "A notebook full of ideas.<br>Nowhere to build from.",
                             "text-3xl md:text-4xl font-bold leading-tight")
                    ui.label(
                        "Most makers keep a running list — a soil-moisture meter, a RAG "
                        "chatbot, a mechanical keyboard. But the ideas live in scattered "
                        "notes. There's no shared place to present them, no easy way to "
                        "see what others are building, and no quick answer to the real "
                        "question: what would it actually take to build several of these "
                        "at once?"
                    ).classes("text-lg text-[#57534E] leading-relaxed")
                with ui.element("div").classes(
                    "vc-reveal vc-d2 vc-card p-7 md:p-9 flex flex-col gap-5"
                ):
                    ui.label("The solution").classes("vc-eyebrow")
                    self._heading(2, "One canvas — from idea to build list.",
                             "text-2xl md:text-3xl font-bold")
                    ui.label(
                        "VentureCanvas gives every idea a home, a community to discover, "
                        "and a collection that does the math for you. Save the projects "
                        "you love and watch their requirements merge into a single, "
                        "deduplicated resource list."
                    ).classes("text-[#57534E] leading-relaxed")
                    for item in [
                        "Publish & present your ideas",
                        "Discover and filter the community gallery",
                        "Curate a personal collection",
                        "Auto-aggregate skills, tools, APIs & hardware",
                    ]:
                        with ui.element("div").classes("flex items-center gap-3"):
                            self._ico("circle-check", "text-[#C2410C] shrink-0", 20)
                            ui.label(item).classes("text-[#44403C]")

    # ----- landing: features bento ------------------------------------------

    def _landing_features(self) -> None:
        with ui.element("section").classes("w-full bg-white"):
            ui.html('<span id="features" class="vc-anchor"></span>', sanitize=False)
            with ui.element("div").classes(
                "mx-auto max-w-7xl px-6 md:px-8 py-20 md:py-28"
            ):
                with ui.element("div").classes(
                    "vc-reveal flex flex-col items-center text-center gap-3 mb-12"
                ):
                    ui.label("Everything in one place").classes("vc-eyebrow")
                    self._heading(2, "Built for makers who ship",
                             "text-3xl md:text-5xl font-bold")
                    ui.label(
                        "Five tools that turn a list of ideas into a plan you can act on."
                    ).classes("text-lg text-[#57534E] max-w-2xl")
                with ui.element("div").classes(
                    "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-5 "
                    "lg:auto-rows-[minmax(186px,auto)]"
                ):
                    self._feature_resource_card()
                    self._feature_card(
                        "lightbulb", "Share your ideas",
                        "Publish a project in minutes — title, description, category, "
                        "and the skills, tools, APIs and hardware it needs.",
                        "md:col-span-2 lg:col-span-2", "vc-d1")
                    self._feature_card(
                        "compass", "Discover & filter",
                        "Browse the whole gallery, newest first, and narrow by category "
                        "in one click.",
                        "lg:col-span-1", "vc-d2")
                    self._feature_card(
                        "bookmark", "Curate collections",
                        "Bookmark anything that sparks an idea into your private shortlist.",
                        "lg:col-span-1", "vc-d3")
                    self._feature_card(
                        "settings-2", "Own & edit your projects",
                        "Your projects, your control — edit any detail or remove what's "
                        "gone stale, anytime.",
                        "md:col-span-2 lg:col-span-4", "vc-d4")

    def _feature_card(self, icon: str, title: str, desc: str,
                      span: str, delay: str) -> None:
        with ui.element("div").classes(
            f"vc-bento vc-reveal {delay} {span} flex flex-col gap-3"
        ):
            with ui.element("div").classes("vc-ico"):
                self._ico(icon, "", 22)
            ui.label(title).classes("vc-head text-lg font-semibold")
            ui.label(desc).classes("text-[#57534E] leading-relaxed")

    def _feature_resource_card(self) -> None:
        with ui.element("div").classes(
            "vc-bento vc-bento-dark vc-reveal md:col-span-2 lg:col-span-2 lg:row-span-2 "
            "flex flex-col gap-4"
        ):
            ui.html(
                '<div class="vc-deco" style="position:absolute;inset:0;'
                "background:radial-gradient(60% 60% at 80% 8%,"
                'rgba(234,88,12,.32),transparent 70%)"></div>',
                sanitize=False,
            )
            with ui.element("div").classes(
                "relative flex items-center justify-between"
            ):
                with ui.element("div").classes("vc-ico vc-ico-light"):
                    self._ico("layers", "", 22)
                with ui.element("span").classes(
                    "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 "
                    "text-xs font-semibold"
                ).style("background:rgba(245,158,11,.18);color:#FBBF24"):
                    ui.label("Signature feature")
            ui.label("Resource Summary").classes(
                "vc-head text-white text-xl font-semibold relative"
            )
            ui.label(
                "Save a handful of projects and we union every requirement across them "
                "— no duplicates — neatly grouped into Skills, Tools, APIs and Hardware. "
                "Your build-everything shopping list, generated automatically."
            ).classes("text-[#D6D3D1] relative leading-relaxed")
            with ui.element("div").classes(
                "relative mt-auto grid grid-cols-2 gap-2 pt-2"
            ):
                for lbl, items in [
                    ("Skills", "Python · soldering · C"),
                    ("Tools", "ESP32 · QMK · Chroma"),
                    ("APIs", "OpenAI · ThingSpeak"),
                    ("Hardware", "Soil sensor · switches"),
                ]:
                    with ui.element("div").classes(
                        "rounded-xl bg-white/5 border border-white/10 p-3 "
                        "flex flex-col gap-1"
                    ):
                        ui.label(lbl).classes(
                            "text-[10px] uppercase tracking-wider text-[#A8A29E] font-semibold"
                        )
                        ui.label(items).classes("text-xs text-[#E7E5E4]")

    # ----- landing: how it works --------------------------------------------

    def _landing_how(self) -> None:
        with ui.element("section").classes("w-full bg-[#FAFAF9]"):
            ui.html('<span id="how" class="vc-anchor"></span>', sanitize=False)
            with ui.element("div").classes(
                "mx-auto max-w-6xl px-6 md:px-8 py-20 md:py-28"
            ):
                with ui.element("div").classes(
                    "vc-reveal flex flex-col items-center text-center gap-3 mb-14"
                ):
                    ui.label("How it works").classes("vc-eyebrow")
                    self._heading(2, "Three steps to your build plan",
                             "text-3xl md:text-4xl font-bold")
                with ui.element("div").classes("grid md:grid-cols-3 gap-10 md:gap-6"):
                    for i, (num, icon, title, desc) in enumerate(_STEPS):
                        with ui.element("div").classes(
                            f"vc-reveal vc-d{i + 1} flex flex-col items-center "
                            "text-center gap-4 px-2"
                        ):
                            ui.html(f'<div class="vc-step-badge">{num}</div>',
                                    sanitize=False)
                            with ui.element("div").classes("vc-ico"):
                                self._ico(icon, "", 22)
                            ui.label(title).classes("vc-head text-xl font-semibold")
                            ui.label(desc).classes(
                                "text-[#57534E] leading-relaxed max-w-xs"
                            )
                with ui.element("div").classes("flex justify-center mt-12"):
                    with ui.link(target="/home").classes(
                        "vc-btn vc-btn-primary no-underline"
                    ):
                        ui.label("Discover projects")
                        self._ico("arrow-right", "", 18)

    # ----- landing: resource-summary spotlight ------------------------------

    def _landing_resource_spotlight(self) -> None:
        with ui.element("section").classes("w-full bg-white"):
            with ui.element("div").classes(
                "mx-auto max-w-7xl px-6 md:px-8 py-20 md:py-28"
            ):
                with ui.element("div").classes(
                    "vc-reveal flex flex-col items-center text-center gap-3 mb-12"
                ):
                    with ui.element("div").classes("vc-chip vc-chip-accent"):
                        ui.label("See it in action")
                    self._heading(2, "Your whole collection, summed up.",
                             "text-3xl md:text-5xl font-bold")
                    ui.label(
                        "Stop tab-hopping between project pages. One view tells you "
                        "every skill to learn, tool to install, API to wire up and "
                        "part to buy."
                    ).classes("text-lg text-[#57534E] max-w-2xl")
                with ui.element("div").classes(
                    "vc-reveal vc-d1 vc-card p-5 md:p-8 grid "
                    "lg:grid-cols-[1fr_auto_1fr] gap-6 lg:gap-8 items-center"
                ):
                    with ui.element("div").classes("flex flex-col gap-3"):
                        ui.label("Before · scattered").classes("vc-eyebrow text-[#A8A29E]")
                        for title, cat, reqs in _SPOTLIGHT_BEFORE:
                            self._spotlight_project(title, cat, reqs)
                    with ui.element("div").classes(
                        "flex lg:flex-col items-center justify-center gap-2"
                    ):
                        ui.html('<span class="vc-merge-arrow">'
                                + self._icon_svg("arrow-right", 24) + "</span>", sanitize=False)
                        ui.label("auto-aggregated").classes(
                            "text-xs text-[#A8A29E] font-medium text-center"
                        )
                    with ui.element("div").classes(
                        "vc-panel-dark p-5 md:p-6 flex flex-col gap-4"
                    ):
                        with ui.element("div").classes("flex items-center justify-between"):
                            with ui.element("div").classes("flex items-center gap-2"):
                                with ui.element("div").classes("vc-ico vc-ico-light").style(
                                    "width:32px;height:32px;border-radius:9px"
                                ):
                                    self._ico("layers", "", 17)
                                ui.label("Resource Summary").classes(
                                    "vc-head text-white font-semibold"
                                )
                            ui.label("3 projects").classes("text-xs text-[#A8A29E]")
                        for lbl, items in _SPOTLIGHT_AFTER:
                            with ui.element("div").classes("flex flex-col gap-1.5"):
                                ui.label(lbl).classes(
                                    "text-[10px] uppercase tracking-wider "
                                    "text-[#A8A29E] font-semibold"
                                )
                                with ui.element("div").classes("flex flex-wrap gap-1.5"):
                                    for it in items:
                                        with ui.element("span").classes(
                                            "vc-chip vc-chip-ondark"
                                        ):
                                            ui.label(it)
                        ui.label(
                            "Skills, tools, APIs & hardware — merged, deduplicated and "
                            "sorted the moment you save."
                        ).classes("text-xs text-[#A8A29E] pt-1")

    def _spotlight_project(self, title: str, cat: str, reqs) -> None:
        with ui.element("div").classes(
            "rounded-xl border border-[#E7E5E4] bg-[#FAFAF9] p-3.5 flex flex-col gap-2"
        ):
            with ui.element("div").classes("flex items-center justify-between gap-2"):
                ui.label(title).classes("text-sm font-semibold text-[#0A0A0A]")
                ui.label(cat).classes("text-[11px] font-medium text-[#C2410C] shrink-0")
            with ui.element("div").classes("flex flex-col gap-1"):
                for lbl, items in reqs:
                    with ui.element("div").classes("flex items-baseline gap-2"):
                        ui.label(lbl).classes(
                            "text-[10px] uppercase tracking-wide text-[#A8A29E] "
                            "font-semibold w-16 shrink-0"
                        )
                        ui.label(items).classes("text-xs text-[#78716C]")

    # ----- landing: social proof --------------------------------------------

    def _landing_social_proof(self) -> None:
        with ui.element("section").classes("w-full bg-[#FAFAF9]"):
            with ui.element("div").classes(
                "mx-auto max-w-7xl px-6 md:px-8 py-20 md:py-28 flex flex-col gap-14"
            ):
                with ui.element("div").classes(
                    "vc-reveal grid grid-cols-3 max-w-3xl mx-auto w-full rounded-2xl "
                    "overflow-hidden border border-[#E7E5E4] bg-white"
                ):
                    for value, suffix, label in [
                        ("80", "+", "project ideas"),
                        ("5", "", "categories"),
                        ("4", "", "resource types unified"),
                    ]:
                        with ui.element("div").classes(
                            "flex flex-col items-center gap-1 p-6 text-center "
                            "border-r last:border-r-0 border-[#E7E5E4]"
                        ):
                            ui.html(
                                '<div class="flex items-baseline justify-center">'
                                f'<span class="vc-stat-num text-3xl md:text-4xl" '
                                f'data-count="{value}">{value}</span>'
                                f'<span class="vc-stat-num text-3xl md:text-4xl">{suffix}</span>'
                                "</div>",
                                sanitize=False,
                            )
                            ui.label(label).classes("text-sm text-[#57534E]")
                with ui.element("div").classes(
                    "vc-reveal flex items-center justify-center gap-2 -mt-8"
                ):
                    ui.html('<span class="vc-live-dot"></span>', sanitize=False)
                    ui.label(
                        "A growing, community-driven project — built in the open."
                    ).classes("text-sm font-medium text-[#15803D]")
                with ui.element("div").classes(
                    "vc-reveal vc-card max-w-3xl mx-auto p-8 md:p-10 flex flex-col gap-4 "
                    "items-center text-center"
                ):
                    self._ico("quote", "text-[#C2410C]", 32)
                    self._heading(
                        3,
                        "“Everybody has a notebook full of project ideas. "
                        "VentureCanvas is the place to record them, share them, and see "
                        "exactly what it takes to build them — together.”",
                        "text-xl md:text-2xl font-semibold leading-snug",
                    )
                    ui.label("— The VentureCanvas team · FHNW").classes(
                        "text-sm text-[#57534E]"
                    )
                with ui.element("div").classes(
                    "vc-reveal flex flex-col items-center gap-8 w-full"
                ):
                    with ui.element("div").classes(
                        "flex flex-col items-center gap-2 text-center"
                    ):
                        ui.label("The team").classes("vc-eyebrow")
                        self._heading(2, "Built by three makers at FHNW",
                                 "text-2xl md:text-3xl font-bold")
                    with ui.element("div").classes(
                        "grid grid-cols-1 sm:grid-cols-3 gap-6 md:gap-8 w-full max-w-3xl"
                    ):
                        for name, role, photo in [
                            ("Mihael", "Co-creator", "team_mihael.png"),
                            ("Eva", "Co-creator", "team_eva.png"),
                            ("Minh", "Co-creator", "team_minh.png"),
                        ]:
                            with ui.link(target=GITHUB_REPO, new_tab=True).classes(
                                "vc-team-card flex flex-col items-center gap-3 no-underline"
                            ):
                                ui.html(
                                    '<span class="vc-ring">'
                                    f'<img src="/static/{photo}" alt="{name}" '
                                    'class="vc-team-photo"></span>',
                                    sanitize=False, tag="span",
                                )
                                with ui.element("div").classes(
                                    "flex flex-col items-center"
                                ):
                                    ui.label(name).classes("vc-head text-lg font-semibold")
                                    ui.label(role).classes("text-sm text-[#57534E]")

    # ----- landing: final CTA -----------------------------------------------

    def _landing_cta(self) -> None:
        guest = not self._auth.is_authenticated
        with ui.element("section").classes("w-full"):
            with ui.element("div").classes("vc-cta-band w-full"):
                ui.html('<div class="vc-cta-glow vc-deco"></div>', sanitize=False)
                with ui.element("div").classes(
                    "relative z-10 mx-auto max-w-3xl px-6 py-20 md:py-28 "
                    "flex flex-col items-center text-center gap-6"
                ):
                    self._heading(2, "Your next build starts with one idea.",
                             "text-white text-4xl md:text-5xl font-bold")
                    ui.label(
                        "Join VentureCanvas free, save the projects that inspire you, "
                        "and get your build list in seconds."
                    ).classes("text-lg text-[#D6D3D1]")
                    with ui.element("div").classes(
                        "flex flex-col sm:flex-row gap-3 pt-2"
                    ):
                        if guest:
                            with ui.link(target="/register").classes(
                                "vc-btn vc-btn-onbrand vc-btn-lg no-underline"
                            ):
                                ui.label("Get started free")
                                self._ico("arrow-right", "", 18)
                            with ui.link(target="/home").classes(
                                "vc-btn vc-btn-onbrand-ghost vc-btn-lg no-underline"
                            ):
                                ui.label("Browse projects")
                        else:
                            with ui.link(target="/home").classes(
                                "vc-btn vc-btn-onbrand vc-btn-lg no-underline"
                            ):
                                ui.label("Go to your dashboard")
                                self._ico("arrow-right", "", 18)
                    ui.label(
                        "No credit card. No setup. Built by students, for builders."
                    ).classes("text-sm text-[#A8A29E]")

    # ----- landing: footer ---------------------------------------------------

    def _landing_footer(self) -> None:
        with ui.element("footer").classes("vc-footer w-full"):
            with ui.element("div").classes(
                "mx-auto max-w-7xl px-6 md:px-8 pt-16 pb-10"
            ):
                with ui.element("div").classes(
                    "grid gap-10 md:grid-cols-[1.6fr_1fr_1fr_1fr]"
                ):
                    with ui.element("div").classes("flex flex-col gap-4 max-w-xs"):
                        ui.html(
                            '<img src="/static/logo.png" alt="VentureCanvas" '
                            'class="vc-logo-white" '
                            'style="height:58px;width:auto;display:block">',
                            sanitize=False,
                        )
                        ui.label(
                            "Share ideas. Build together. Create impact."
                        ).classes("text-sm text-[#A8A29E]")
                        with ui.element("div").classes("flex items-center gap-2"):
                            ui.html('<span class="vc-live-dot"></span>', sanitize=False)
                            ui.label("Community-driven · open source (MIT)").classes(
                                "text-xs text-[#A8A29E]"
                            )
                    self._footer_col("Product", [
                        ("Discover", "/home"), ("Categories", "#categories"),
                        ("How it works", "#how"), ("Resource Summary", "#features"),
                    ])
                    self._footer_col("Account", [
                        ("Log in", "/login"), ("Register", "/register"),
                        ("My collection", "/collection"),
                    ])
                    self._footer_col("Project", [
                        ("GitHub", GITHUB_REPO), ("License (MIT)", GITHUB_REPO),
                    ])
                with ui.element("div").classes(
                    "mt-12 pt-6 border-t border-white/10 flex flex-col md:flex-row "
                    "items-center justify-between gap-3"
                ):
                    ui.label("© 2026 VentureCanvas · MIT-licensed").classes(
                        "text-sm text-[#78716C]"
                    )
                    ui.label(
                        "Built at FHNW · Object-Oriented Programming · Spring 2026 (FS26)"
                    ).classes("text-sm text-[#78716C]")
                    with ui.link(target=GITHUB_REPO, new_tab=True).classes(
                        "no-underline"
                    ).props('aria-label="VentureCanvas on GitHub"'):
                        self._ico("github", "text-[#A8A29E]", 22)

    def _footer_col(self, title: str, links) -> None:
        with ui.element("div").classes("flex flex-col gap-3"):
            ui.html(f"<h4>{title}</h4>", sanitize=False)
            for label, target in links:
                ui.link(label, target).classes("text-sm")

    # ------------------------------------------------------------------ home

    def _home_page(self) -> None:
        self._header()
        # Load-more is contextual: the All view (or any search across
        # everything) bumps in big chunks so two clicks reveal the full
        # ~80 catalog. A picked category starts with a tight 2x4 grid and
        # reveals slowly, four cards at a time.
        ALL_INITIAL, ALL_CHUNK = 12, 36
        CAT_INITIAL, CAT_CHUNK = 8, 4
        # Single mutable view-model for this page. Every handler below edits
        # `state` and calls refresh() to re-render — there is no other source
        # of truth for what the grid shows.
        state = {
            "category": None,        # Optional[Category]; None = show all
            "search": "",
            "sort": "newest",        # "newest" | "oldest" | "az"
            "visible": ALL_INITIAL,  # cards currently shown by the load-more grid
        }

        def initial_size() -> int:
            return CAT_INITIAL if state["category"] is not None else ALL_INITIAL

        def chunk_size() -> int:
            return CAT_CHUNK if state["category"] is not None else ALL_CHUNK

        with ui.column().classes("w-full p-6 gap-4 items-start"):
            ui.label("Discover innovation projects").classes("text-2xl font-bold")

            # Toolbar — search + sort. Lives outside the refreshable region so
            # typing never steals focus from the input.
            with ui.row().classes("w-full gap-3 items-center"):
                def on_search_change(e) -> None:
                    new_val = (e.value or "").strip()
                    if new_val == state["search"]:
                        return
                    state["search"] = new_val
                    state["visible"] = initial_size()
                    refresh()

                search_input = ui.input(
                    placeholder="Search title or description…",
                    on_change=on_search_change,
                ).props(
                    "clearable dense outlined debounce=300"
                ).classes("flex-grow max-w-md")

                def on_sort_change(e) -> None:
                    state["sort"] = e.value
                    state["visible"] = initial_size()
                    refresh()

                ui.select(
                    {"newest": "Newest", "oldest": "Oldest", "az": "A–Z"},
                    value="newest",
                    on_change=on_sort_change,
                ).props("dense outlined").classes("w-40")

            # The only region that re-renders: refresh() clears `results` and
            # rebuilds the chips + grid from the current `state`.
            results = ui.column().classes("w-full gap-4")

            def select_cat(target) -> None:
                state["category"] = target
                state["visible"] = initial_size()
                refresh()

            def render_chip(label: str, target) -> None:
                is_active = state["category"] == target
                props = (
                    "unelevated no-caps color=primary"
                    if is_active
                    else "outline no-caps color=grey-8"
                )
                ui.button(
                    label, on_click=lambda t=target: select_cat(t)
                ).props(props).classes("px-2")

            def clear_filters() -> None:
                state["category"] = None
                state["search"] = ""
                state["visible"] = ALL_INITIAL
                search_input.value = ""
                refresh()

            def render_grid() -> None:
                rows = self._home.list_filtered(
                    category=state["category"],
                    search=state["search"],
                    sort=state["sort"],
                )
                total = len(rows)
                if total == 0:
                    with ui.column().classes(
                        "w-full items-center py-12 gap-2"
                    ):
                        ui.label(
                            "No projects match your search."
                        ).classes("text-grey-7")
                        ui.button(
                            "Clear filters", on_click=clear_filters
                        ).props("flat no-caps color=primary")
                    return

                visible = min(state["visible"], total)
                # Responsive grid: 1 col on phone, 2 on tablet, 3 on small
                # desktop, 4 on wide screens — same look for All and filtered.
                with ui.element("div").classes(
                    "w-full grid grid-cols-1 sm:grid-cols-2 "
                    "md:grid-cols-3 lg:grid-cols-4 gap-4"
                ):
                    for p in rows[:visible]:
                        self._render_grid_card(p)

                with ui.row().classes(
                    "w-full items-center justify-center gap-3 mt-2"
                ):
                    ui.label(
                        f"Showing {visible} of {total}"
                    ).classes("text-sm text-grey-7")
                    if visible < total:
                        def load_more() -> None:
                            state["visible"] = min(
                                state["visible"] + chunk_size(), total
                            )
                            refresh()
                        ui.button(
                            "Load more", on_click=load_more
                        ).props(
                            "flat no-caps color=grey-7"
                        ).classes("text-sm")

            def refresh() -> None:
                results.clear()
                with results:
                    with ui.row().classes(
                        "gap-2 items-center flex-wrap mb-2"
                    ):
                        render_chip("All", None)
                        for cat in self._home.available_categories():
                            render_chip(cat.value, cat)
                    render_grid()

            refresh()

    def _render_project_card(self, project: Project) -> None:
        """Fixed-width (w-80) card used by the My-Projects row.

        Sibling of :meth:`_render_grid_card`, which instead stretches to fill
        a responsive grid cell. The whole card is clickable; the description
        is truncated to ~140 chars with an ellipsis.
        """
        with ui.card().classes("w-80 flex flex-col gap-2 vc-hovercard").on(
            "click", lambda e=None, pid=project.id: ui.navigate.to(f"/project/{pid}")
        ):
            ui.label(project.category.value).classes(
                "self-start text-xs bg-[#0A0A0A] text-white rounded-full "
                "px-2.5 py-0.5 font-medium"
            )
            ui.label(project.title).classes("text-lg font-bold")
            ui.label(
                project.description[:140]
                + ("…" if len(project.description) > 140 else "")
            ).classes("text-sm text-[#57534E]")
            ui.link("View project →", f"/project/{project.id}").classes(
                "text-sm font-semibold text-[#C2410C] no-underline mt-1"
            )

    def _render_grid_card(self, project: Project) -> None:
        """Stretch-to-cell card used by the home-page grid.

        Carries a small pitch-black category pill at the top so the All
        view (which mixes categories) stays scannable. The whole card is
        clickable; ``flex-grow`` on the description keeps the "View"
        affordance aligned at the bottom of each row.
        """
        with ui.card().classes("w-full h-full flex flex-col gap-2 vc-hovercard").on(
            "click", lambda e=None, pid=project.id: ui.navigate.to(f"/project/{pid}")
        ):
            ui.label(project.category.value).classes(
                "self-start text-xs bg-[#0A0A0A] text-white "
                "rounded-full px-3 py-1 font-medium"
            )
            ui.label(project.title).classes("text-lg font-bold")
            ui.label(
                project.description[:140]
                + ("…" if len(project.description) > 140 else "")
            ).classes("text-sm text-[#57534E] flex-grow")
            ui.link("View project →", f"/project/{project.id}").classes(
                "self-start text-sm font-semibold text-[#C2410C] no-underline mt-1"
            )

    # ------------------------------------------------------------------ login / register

    def _login_page(self) -> None:
        self._header()
        with ui.card().classes("max-w-md mx-auto mt-12 p-6"):
            ui.label("Login").classes("text-xl font-bold mb-2")
            email = ui.input("Email").classes("w-full")
            password = ui.input("Password", password=True, password_toggle_button=True).classes("w-full")

            def submit() -> None:
                # Pattern used by every form: call the controller, turn any
                # typed service error into a toast, otherwise notify + navigate.
                try:
                    self._auth.login(email=email.value, password=password.value)
                except AuthError as exc:
                    ui.notify(str(exc), type="negative")
                    return
                ui.notify("Logged in.", type="positive")
                ui.navigate.to("/home")

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
                ui.link("← Back to home", "/home")
            return

        # Precompute everything the template branches on, so the layout below
        # stays declarative.
        cat = project.category.value
        icon = _CATEGORY_ICON.get(cat, "layers")   # fall back to a generic icon
        reqs = [
            ("Skills", project.required_skills),
            ("Tools", project.required_tools),
            ("APIs", project.required_apis),
            ("Hardware", project.required_hardware),
        ]
        has_reqs = any(v and v.strip() for _label, v in reqs)  # any non-empty list?
        is_owner = self._project.is_owner(project)             # show edit/delete only to the owner

        with ui.column().classes("w-full max-w-5xl mx-auto p-6 md:p-8 gap-6"):
            ui.link("← All projects", "/home").classes("vc-appbar-link text-sm")

            # ---- header card -------------------------------------------------
            with ui.card().classes("w-full p-6 md:p-8 gap-3"):
                with ui.row().classes("items-center gap-3"):
                    with ui.element("div").classes("vc-ico"):
                        self._ico(icon, "", 22)
                    ui.label(cat).classes(
                        "bg-[#0A0A0A] text-white rounded-full px-3 py-1 "
                        "text-xs font-semibold"
                    )
                ui.label(project.title).classes("vc-head text-3xl md:text-4xl font-bold")
                ui.label(project.description).classes(
                    "text-[#57534E] leading-relaxed whitespace-pre-wrap max-w-3xl"
                )

            # ---- requirements + action sidebar -------------------------------
            with ui.element("div").classes(
                "w-full grid lg:grid-cols-[1fr_300px] gap-6 items-start"
            ):
                with ui.card().classes("w-full p-6 md:p-7 gap-4"):
                    ui.label("What it takes to build this").classes(
                        "vc-head text-lg font-semibold"
                    )
                    if has_reqs:
                        for label, raw in reqs:
                            self._render_requirement(label, raw)
                    else:
                        ui.label("No requirements listed yet.").classes(
                            "text-[#78716C]"
                        )

                with ui.card().classes("w-full p-6 gap-3"):
                    if self._auth.is_authenticated:
                        ui.label("Save & build").classes(
                            "vc-head text-base font-semibold"
                        )
                        ui.label(
                            "Add this to your collection to fold its requirements "
                            "into your resource summary."
                        ).classes("text-sm text-[#78716C]")
                        ui.button(
                            "Add to collection",
                            on_click=lambda: self._handle_add_to_collection(project.id),
                        ).props("color=primary unelevated no-caps").classes("w-full")
                        if is_owner:
                            ui.separator().classes("my-1")
                            ui.label("Owner tools").classes(
                                "text-xs uppercase tracking-wider text-[#78716C] "
                                "font-semibold"
                            )
                            ui.button(
                                "Edit project",
                                on_click=lambda: ui.navigate.to(
                                    f"/project/{project.id}/edit"
                                ),
                            ).props("outline color=primary no-caps").classes("w-full")
                            ui.button(
                                "Delete",
                                on_click=lambda: self._handle_delete_project(project.id),
                            ).props("outline color=negative no-caps").classes("w-full")
                    else:
                        ui.label("Want to build this?").classes(
                            "vc-head text-base font-semibold"
                        )
                        ui.label(
                            "Join VentureCanvas to save projects and auto-aggregate "
                            "everything you'll need."
                        ).classes("text-sm text-[#78716C]")
                        ui.button(
                            "Create free account",
                            on_click=lambda: ui.navigate.to("/register"),
                        ).props("color=primary unelevated no-caps").classes("w-full")
                        ui.button(
                            "Log in",
                            on_click=lambda: ui.navigate.to("/login"),
                        ).props("flat color=primary no-caps").classes("w-full")

            # ---- more in this category --------------------------------------
            # Same-category projects, newest first, excluding the one being
            # viewed, capped at four for the "More in …" strip.
            related = [
                p
                for p in self._home.list_filtered(
                    category=project.category, search="", sort="newest"
                )
                if p.id != project.id
            ][:4]
            if related:
                ui.label(f"More in {cat}").classes("vc-head text-xl font-semibold mt-2")
                with ui.element("div").classes(
                    "w-full grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
                ):
                    for related_project in related:
                        self._render_grid_card(related_project)

    def _render_requirement(self, label: str, raw_value: str) -> None:
        # Turn one comma-separated field into a labelled row of chips; render
        # nothing if it's blank.
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
        # Map each typed service error to the right toast: a real problem is a
        # "warning"; an already-saved project is just "info", not a failure.
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
        ui.navigate.to("/home")

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

        # view() returns both halves at once: the saved projects (left) and the
        # deduplicated cross-project resource summary (right sidebar).
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
                                # pid=project.id binds the current id as a default
                                # arg, capturing it now — otherwise every button
                                # would close over the last loop value.
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

            # Right sidebar: the signature feature — every requirement across
            # the whole collection, merged and deduplicated into four lists.
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
