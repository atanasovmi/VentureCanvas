# VentureCanvas — Rebuild Plan

Total codebase overhaul. Delete the current Flask + Vue repo. Build a Python-only NiceGUI app whose **single goal is to score as high as possible against the Guidelines + Bewertungsraster (§0)**, written in OOP throughout, with the Pizza-Projekt as a style reference (§1).

**Deadline:** 31. Mai 2026, 23:55 — Moodle PDF (presentation + GitHub URL). 72 h grace capped at grade 4.0; later = 1.0.

---

## 0 · Authority (highest priority)

The **Guidelines PDF** and **Bewertungsraster** are the only documents that decide our grade. Everything in this plan exists to serve them. If anything here conflicts with them, they win.

- Guidelines: `C:/Users/mihae/OneDrive - FHNW/Semester 2/OOP/SS26_Guidelines_Programmierprojekt (1).pdf`
- Bewertungsraster: `C:/Users/mihae/OneDrive - FHNW/Semester 2/OOP/SS26_Assessment_Programmierprojekt.xlsm`

### Rubric — 100 points, pass ≥ 50

| Category | Weight | What it actually grades |
|---|---|---|
| Funktionalität | 30 % | App runs without errors · all promised features work · UI is clear, consistent, navigable |
| Anwendung der Python-Lehrinhalte | 30 % | **OOP + ORM + clean layer separation + business logic and error handling in the right layers** |
| Präsentation | 20 % | Slides clear · 15-min live demo · correct Q&A with line-by-line code explanation |
| Dokumentation | 10 % | README has User Stories · Use Cases · Libraries · Work Split · Design Decisions |
| Projektmanagement & Engagement | 10 % | Every team member has substantive GitHub contributions |

### Guidelines hard rules

- Python web app (no CLI); **NiceGUI is the mandated frontend framework**
- Three-layer architecture (browser thin client → Python server + OOP business logic → ORM-backed DB)
- **OOP throughout — see §0.1**
- ORM (we use SQLModel)
- Team of 3 students, all contributing via GitHub
- 15-minute presentation covering: topic justification · goals & features · project management · live demo · Q&A
- Students must explain the code line-by-line during Q&A
- Pizza-Projekt (§1) is the reference template

### 0.1 · OOP is a hard requirement

30 % of the grade is tied to "OOP-Strukturen korrekt und sinnvoll eingesetzt". Rules that apply to the whole codebase:

- **Every file under `domain/`, `data_access/`, `services/`, and `ui/controllers.py` is class-based.** No module-level CRUD functions, no "services as plain function module".
- Each service class takes its DAOs / collaborators in `__init__` (constructor injection). No module-level singletons, no globals for mutable state.
- Helpers are methods on the class that owns the behaviour (use `_private` names if internal), not loose module-level functions.
- Only `__main__.py`, `styles.css`, `pytest.ini`, `pyproject.toml`, and test files may have top-level code.
- The named patterns in §6 (MVC · Repository/DAO · Facade · Composition Root) must be visible both in the code and in module docstrings — the grader uses these as ticks during Q&A.

---

## 1 · Reference project

Guide: `C:/Users/mihae/PycharmProjects/Pizzeria-Reference-Project/`. Use it for **code style, the layer-separation idea, and the level of simplicity** — not as a template to clone verbatim. Our domain is different (a community content platform, not a transactional ordering app), so copy patterns only where they actually help us. Flex on file names, method signatures, tech choices, and README wording whenever our domain suggests something simpler.

---

## 2 · Stack

- Python 3.11+
- `nicegui` · `sqlmodel` · `python-dotenv` · `pytest`
- Password hashing via stdlib `hashlib.pbkdf2_hmac` + `secrets` (zero external deps; same PBKDF2-SHA256 algorithm Werkzeug would have used, but no library to install)
- SQLite, auto-created + seeded on first run via `Database.init_schema_and_seed()`

Nothing else. No Flask, JWT, REST, Tailwind, Neon, Reportlab, Marshmallow, Quasar.

---

## 3 · Features (the only ones we build)

1. Register
2. Log in
3. Log out
4. Browse all projects
5. Filter projects by category (All · IoT · AI · Web · Mobile · Hardware)
6. View one project's detail
7. Create a project (owned by the creator)
8. Edit my own project
9. Delete my own project
10. Add a project to my Collection
11. Remove a project from my Collection
12. See my Collection with aggregated required skills / tools / APIs / hardware

**Explicitly cut** (not in Guidelines, not in Pizza, no rubric payoff):
comments · free-text search · pagination · profile edit · admin page · role system · dark-theme animation.

---

## 4 · Kill list (from current repo)

Delete wholesale before writing a single new line:

- `backend/` (entire Flask app)
- `frontend/` (entire Vue/Quasar SPA + lockfile)
- `docs/mvc-analysis.md` · `docs/class-diagram.md`
- `README.md` (old-stack; will be rewritten from scratch)

---

## 5 · Target layout (Pizza-inspired — flex on details)

The four layers below and the single package root are the important part. File names, method signatures, and where exactly a helper lives inside a layer are the agent's / team's call — copy Pizza where it fits, diverge where our domain is cleaner.

```
venturecanvas/
├── __init__.py
├── __main__.py                       # py -m venturecanvas
├── application.py                    # VentureCanvasApplication composition root
├── domain/
│   ├── __init__.py
│   └── models.py                     # SQLModel: User, Project, CollectionItem
├── data_access/
│   ├── __init__.py
│   ├── db.py                         # Database facade + session_scope + init_schema_and_seed
│   ├── dao.py                        # BaseDAO + UserDAO + ProjectDAO + CollectionDAO
│   └── seed.py                       # ProjectSeeder class
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   ├── project_service.py
│   └── collection_service.py
├── ui/
│   ├── __init__.py
│   ├── controllers.py                # AuthController · HomeController · ProjectController · CollectionController
│   └── pages.py                      # Pages class with register()
└── static/
    └── styles.css
tests/
├── __init__.py
├── conftest.py
├── test_unit.py                      # services only
├── test_db.py                        # DAOs + ORM
└── test_integration.py               # controller end-to-end
docs/
├── architecture-diagrams/
│   ├── uml_class_architecture.png
│   ├── uml_use_case_diagram.png
│   └── er_diagram.png
└── ui-images/                        # screenshots added before submission
pyproject.toml
pytest.ini
requirements.txt
.env.example
.gitignore
LICENSE
README.md
Plan.md
```

---

## 6 · Patterns we claim (rubric ticks)

Name these in README and in module docstrings:

- **MVC** — `domain/` (Model) · `ui/pages.py` (View) · `ui/controllers.py` (Controller)
- **Repository / DAO** — `data_access/dao.py`
- **Facade** — `Database` class in `data_access/db.py`
- **Composition Root** — `VentureCanvasApplication` in `application.py`

Do not claim Strategy or Adapter — they do not fit VentureCanvas's domain.

---

## 7 · Data validation

All validation on SQLModel `Field(...)` declarations — no separate validator library.

- `User.username` — `min_length=3, max_length=40`, unique
- `User.email` — unique, indexed, `max_length=120`
- `User.password_hash` — stored only (plaintext hashed via `werkzeug.security` inside `AuthService`)
- `Project.title` — `min_length=2, max_length=200`
- `Project.description` — `min_length=1`, `max_length=2000`
- `CollectionItem` — `__table_args__ = (UniqueConstraint("user_id", "project_id"),)` so a project can't be added twice

---

## 8 · Tests (≥ 12)

Three-file split (unit / db / integration) is a sensible default — feel free to diverge if a different grouping fits better.

- `test_unit.py` — service layer, pure business logic
  - register success · register duplicate · login success · login wrong password · project create valid · project create invalid · collection add dedup · collection aggregation
- `test_db.py` — DAOs on in-memory SQLite
  - project insert/load · collection unique constraint enforced · seed populates tables
- `test_integration.py` — controller end-to-end
  - register → login → create project → add to collection → aggregation visible
  - edit own project / cannot edit someone else's
  - delete own project

`pytest` green is a release gate.

---

## 9 · README outline

Covers every section the Guidelines require (User Stories · Use Cases · Libraries · Work Distribution · Design Decisions). Pizza's README is a reference for tone and shape — trim, merge or reorder sections wherever ours reads more naturally.

1. Title + UI banner screenshot
2. Problem / Scenario
3. User Stories (12 items, "Als … möchte ich … damit …" form, one per §3 feature)
4. Use Cases (one table per feature: Actor · Pre-condition · Main flow · Post-condition)
5. Architecture (layers + named patterns) + UML class diagram (`docs/architecture-diagrams/uml_class_architecture.png`)
6. Database & ORM + ER diagram (`docs/architecture-diagrams/er_diagram.png`)
7. Project Requirements — how we fulfil each: NiceGUI · Data Validation · ORM
8. Used Libraries (name · version · purpose)
9. Repository Structure (ASCII tree matching §5)
10. How to Run (`py -m venturecanvas`)
11. Testing (test counts + `pytest`)
12. UI Screenshots (`docs/ui-images/`)
13. Team & Contributions (table: Name · Owned features · GitHub handle)
14. License (MIT)

---

## 10 · Team ownership

Three students, three slices. Each member must have ≥ 5 substantive PRs under their own GitHub account. PRs merged by a **different** teammate (cross-review evidence).

| Student | Owns | Q&A readiness |
|---|---|---|
| A | Auth (models User, UserDAO, AuthService, AuthController, Login + Register pages) | Explains auth flow + password hashing |
| B | Projects (Project model, ProjectDAO, ProjectService, Home + Detail + MyProjects pages) | Explains CRUD + ownership check + SQLModel validation |
| C | Collection (CollectionItem model, CollectionDAO, CollectionService, Collection page + aggregation) + `docs/` diagrams + `styles.css` | Explains aggregation + DB facade + ER diagram |

`application.py`, `__main__.py`, `db.py`, tests, README are split proportionally during the rebuild.

---

## 11 · Presentation (20 %)

15 minutes live. Required sections: topic justification · goals & features · project management (work split, highlights, challenges) · live demo · Q&A. Each student must answer line-by-line questions on the files in their slice (see §10).

Deliverables before the day: slide deck PDF · at least one full team dry-run · submission PDF uploaded to Moodle with GitHub URL.

---

## 12 · Release checklist

Everything must be true at submission time.

- [ ] Current `backend/` + `frontend/` + `docs/mvc-analysis.md` + `docs/class-diagram.md` deleted
- [ ] `venturecanvas/` package matches §5 layout
- [ ] `py -m venturecanvas` launches NiceGUI; all 12 features in §3 work end-to-end from a fresh clone after `pip install -r requirements.txt`
- [ ] First launch auto-creates SQLite DB and seeds a demo user + 5–6 projects
- [ ] `pytest` green with ≥ 12 tests across `test_unit.py` / `test_db.py` / `test_integration.py`
- [ ] All four named patterns (§6) mentioned in module docstrings + README
- [ ] Every layer file (except `__main__.py`, test files, config files) is class-based with no module-level CRUD or helper functions (§0.1)
- [ ] Every SQLModel class has explicit `Field(...)` validation
- [ ] README has all 14 sections (§9); no "TBD" placeholders
- [ ] `docs/architecture-diagrams/` has UML class, use-case, ER as PNG
- [ ] `docs/ui-images/` has one screenshot per main page
- [ ] `git shortlog -sne` shows three real humans, each with ≥ 5 substantive commits
- [ ] Every PR merged by a teammate other than its author
- [ ] Slide deck PDF rehearsed once; Moodle submission ready
