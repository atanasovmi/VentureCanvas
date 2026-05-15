"""VentureCanvas — NiceGUI + SQLModel community content platform.

Top-level package. The application is organised into four layers that
depend strictly downward:

    ui ──▶ services ──▶ data_access ──▶ domain

Named patterns (see Plan.md §6):

* **MVC** — :mod:`venturecanvas.domain` (Model),
  :mod:`venturecanvas.ui.pages` (View),
  :mod:`venturecanvas.ui.controllers` (Controller).
* **Repository / DAO** — :mod:`venturecanvas.data_access.dao`.
* **Facade** — :class:`venturecanvas.data_access.db.Database`.
* **Composition Root** —
  :class:`venturecanvas.application.VentureCanvasApplication`.
"""
