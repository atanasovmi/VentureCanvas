# 🚀 VentureCanvas
## Project description 

A community-driven platform for innovation projects
This web platform serves as a central hub where users can present, discover, and further develop their innovative projects.

Users can upload their own projects and present them in detail, including descriptions, files, and additional information. At the same time, they can browse through other users’ projects and find inspiration.

A central component of the platform is interaction within the community: projects can be commented on, discussed, and rated. Users can purchase and download projects or associated files to reuse them or use them as a basis for their own developments. Overall, the platform combines presentation, collaboration, and monetization.



## Inspiration
Many people have a notebook full of project ideas—a soil moisture meter, a RAG chatbot, a mechanical keyboard—but no central place where they can record them, present them, or figure out what it would cost to bring several of these ideas to life at once in terms of parts, services, and expertise.

VentureCanvas solves exactly this problem: a small community gallery where every user can publish their own projects and collect interesting ideas from others. The “Collection” view does the heavy lifting: it summarizes the required skills, tools, APIs, and hardware for all saved projects, so the curator can see the entire shopping list at a glance.



## 1 · User Stories 

Twelve features, twelve user stories — one per row in §4.

| # | Story |
|---|---|
| 1 | As a visitor, I want to **register an account** so that I can contribute and curate. |
| 2 | As a returning user, I want to **log in** so that my projects and collection are restored. |
| 3 | As a logged-in user, I want to **log out** so that nobody else can use my browser session. |
| 4 | As any visitor, I want to **browse all projects** so that I can discover what others are building. |
| 5 | As any visitor, I want to **filter projects by category** (IoT · AI · Web · Mobile · Hardware) so that I can narrow the list to what interests me. |
| 6 | As any visitor, I want to **see a project's details** so that I understand what's required to build it. |
| 7 | As a logged-in user, I want to **create a project** so that the community can see what I'm working on. |
| 8 | As the owner of a project, I want to **edit** it so that I can keep its description current. |
| 9 | As the owner of a project, I want to **delete** it so that outdated ideas don't clutter the gallery. |
| 10 | As a logged-in user, I want to **add a project to my collection** so that I can come back to it later. |
| 11 | As a logged-in user, I want to **remove a project from my collection** so that my shortlist stays clean. |
| 12 | As a logged-in user, I want to see **my collection plus a resource summary** so that I know which skills, tools, APIs and hardware my whole shortlist requires. |

---

## 2 · Use Cases 

Each use case maps one-to-one to the story of the same number.

### UC-1 — Register
| | |
|---|---|
| **Actor** | Visitor |
| **Pre-condition** | No active session in the browser |
| **Main flow** | Open `/register` → fill username, email, password → submit → account is stored with a PBKDF2 hash → user is redirected to `/login`. |
| **Post-condition** | A new `User` row exists with a hashed password. |

### UC-2 — Log in
| | |
|---|---|
| **Actor** | Registered user |
| **Pre-condition** | An account with that email exists |
| **Main flow** | Open `/login` → enter email + password → `AuthService.authenticate` verifies the PBKDF2 hash → `SessionState.login` stores `user_id` in the browser storage → redirect to `/`. |
| **Post-condition** | The browser is authenticated until logout. |

### UC-3 — Log out
| | |
|---|---|
| **Actor** | Logged-in user |
| **Pre-condition** | Authenticated session |
| **Main flow** | Click *Logout* in the header → `SessionState.logout` clears the browser storage → redirect to `/`. |
| **Post-condition** | The browser is anonymous again. |

### UC-4 — Browse projects
| | |
|---|---|
| **Actor** | Any visitor |
| **Pre-condition** | None |
| **Main flow** | Open `/` → `HomeController.list()` calls `ProjectService.list()` → every project is rendered as a card, newest first. |
| **Post-condition** | The home grid reflects the current DB state. |

### UC-5 — Filter by category
| | |
|---|---|
| **Actor** | Any visitor |
| **Pre-condition** | Home page visible |
| **Main flow** | Click a category chip → `HomeController.list(category=…)` → only projects of that category appear. |
| **Post-condition** | The filter is active until the user clicks *All* or another chip. |

### UC-6 — View project detail
| | |
|---|---|
| **Actor** | Any visitor |
| **Pre-condition** | The target project exists |
| **Main flow** | Click a project card → navigate to `/project/{id}` → `ProjectService.get` loads the record → title, description, category and requirement chips render. |
| **Post-condition** | The detail page is shown; if the viewer owns the project, *Edit* and *Delete* buttons appear. |

### UC-7 — Create a project
| | |
|---|---|
| **Actor** | Logged-in user |
| **Pre-condition** | Authenticated session |
| **Main flow** | Open `/project/new` → fill title, description, category, requirements → submit → `ProjectService.create` validates and persists → redirect to the new project's detail page. |
| **Post-condition** | A new `Project` row exists owned by the caller. |

### UC-8 — Edit my project
| | |
|---|---|
| **Actor** | Project owner |
| **Pre-condition** | The caller owns the target project |
| **Main flow** | Open `/project/{id}/edit` → change any field → submit → `ProjectService.update` re-checks ownership and validates title/description → redirect back to detail. |
| **Post-condition** | The record is updated and `updated_at` is refreshed. |

### UC-9 — Delete my project
| | |
|---|---|
| **Actor** | Project owner |
| **Pre-condition** | The caller owns the target project |
| **Main flow** | On `/project/{id}` click *Delete* → `ProjectService.delete` re-checks ownership → ORM cascade removes related `CollectionItem` rows → redirect home. |
| **Post-condition** | The project and any of its collection links are gone. |

### UC-10 — Add to collection
| | |
|---|---|
| **Actor** | Logged-in user |
| **Pre-condition** | Authenticated session, target project exists |
| **Main flow** | On `/project/{id}` click *Add to collection* → `CollectionService.add` checks for duplicates → inserts a `CollectionItem`. |
| **Post-condition** | The project appears on `/collection` and contributes to the summary. |

### UC-11 — Remove from collection
| | |
|---|---|
| **Actor** | Logged-in user |
| **Pre-condition** | The project is currently in the user's collection |
| **Main flow** | On `/collection` click *Remove* → `CollectionService.remove` deletes the `CollectionItem`. |
| **Post-condition** | The project and its tokens are no longer in the summary. |

### UC-12 — View collection with aggregation
| | |
|---|---|
| **Actor** | Logged-in user |
| **Pre-condition** | Authenticated session |
| **Main flow** | Open `/collection` → `CollectionService.summary` splits each saved project's four comma-separated requirement fields → unions the tokens → returns sorted lists for Skills, Tools, APIs and Hardware → the UI renders them as chips next to the list of saved projects. |
| **Post-condition** | The summary card reflects the current collection contents. |

---
