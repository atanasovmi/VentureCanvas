# VentureCanvas
## Project description 

A community-driven platform for innovation projects
This web platform serves as a central hub where users can present, discover, and further develop their innovative projects.

Users can upload their own projects and present them in detail, including descriptions, files, and additional information. At the same time, they can browse through other users’ projects and find inspiration.

A central component of the platform is interaction within the community: projects can be commented on, discussed, and rated. Users can purchase and download projects or associated files to reuse them or use them as a basis for their own developments. Overall, the platform combines presentation, collaboration, and monetization.



## Inspiration
Many people have a notebook full of project ideas—a soil moisture meter, a RAG chatbot, a mechanical keyboard—but no central place where they can record them, present them, or figure out what it would cost to bring several of these ideas to life at once in terms of parts, services, and expertise.

VentureCanvas solves exactly this problem: a small community gallery where every user can publish their own projects and collect interesting ideas from others. The “Collection” view does the heavy lifting: it summarizes the required skills, tools, APIs, and hardware for all saved projects, so the curator can see the entire shopping list at a glance.



## User Stories (Formatierung noch herausfinden!!)

### 1. Login

**Als Nutzer möchte ich mich auf der Plattform einloggen.**
**Beschreibung:** Die Anwendung ermöglicht registrierten Nutzern, sich mit ihren Zugangsdaten zu authentifizieren.
**Input:** E-Mail, Passwort
**Output:** Benutzersitzung gestartet (intern: User-Objekt)

---

### 2. Profil anzeigen

Als Nutzer möchte ich mein Profil ansehen.
Beschreibung: Die Anwendung zeigt die persönlichen Informationen und Aktivitäten des Nutzers an.
Input: Benutzer-ID (aus der Sitzung)
Output: Profildaten angezeigt (intern: User-Profil-Daten)

---

### 3. Projekte anzeigen

Als Nutzer möchte ich nach dem Login verfügbare Projekte sehen.
Beschreibung: Die Anwendung zeigt eine Liste aller verfügbaren Projekte an.
Input: Benutzersitzung
Output: Projektliste angezeigt (intern: Liste[Projekt])

---

### 4. Projekte suchen

Als Nutzer möchte ich nach Projekten suchen.
Beschreibung: Die Anwendung filtert Projekte basierend auf einem Suchbegriff.
Input: Suchbegriff
Output: Gefilterte Projektliste (intern: Liste[Projekt])

---

### 5. Projektdetails anzeigen

Als Nutzer möchte ich detaillierte Informationen zu einem Projekt sehen.
Beschreibung: Die Anwendung zeigt Beschreibung, Dateien und Metadaten eines Projekts an.
Input: Projekt-ID
Output: Projektdetails angezeigt (intern: Projekt-Objekt)

---

### 6. Projekt kommentieren

Als Nutzer möchte ich ein Projekt kommentieren.
Beschreibung: Die Anwendung ermöglicht es Nutzern, Kommentare zu einem Projekt hinzuzufügen.
Input: Projekt-ID, Kommentartext
Output: Kommentar gespeichert und angezeigt (intern: Kommentar-Objekt)

---

### 7. Projekt bewerten

Als Nutzer möchte ich ein Projekt bewerten.
Beschreibung: Die Anwendung ermöglicht es Nutzern, eine Bewertung abzugeben.
Input: Projekt-ID, Bewertungswert
Output: Bewertung gespeichert (intern: Bewertungs-Objekt)

---

### 8. Projekt kaufen

Als Nutzer möchte ich ein Projekt oder dessen Dateien kaufen.
Beschreibung: Die Anwendung verarbeitet den Kauf von Projektinhalten.
Input: Projekt-ID, Zahlungsinformationen
Output: Kaufbestätigung (intern: Bestell-Objekt)

---

### 9. Projektdateien herunterladen

Als Nutzer möchte ich gekaufte Projektdateien herunterladen.
Beschreibung: Die Anwendung ermöglicht den Zugriff auf Dateien nach dem Kauf.
Input: Kauf-ID
Output: Datei-Download (intern: Dateidaten)

---

### 10. Projekt hochladen

Als Nutzer/Ersteller möchte ich ein neues Projekt hochladen.
Beschreibung: Die Anwendung ermöglicht es Nutzern, Projekte zu erstellen und zu veröffentlichen.
Input: Projekttitel, Beschreibung, Dateien
Output: Projekt erstellt (intern: Projekt-Objekt)

---

### 11. Projekt bearbeiten

Als Nutzer/Ersteller möchte ich mein Projekt bearbeiten.
Beschreibung: Die Anwendung ermöglicht das Aktualisieren von Projektdaten.
Input: Projekt-ID, aktualisierte Daten
Output: Projekt aktualisiert (intern: Projekt-Objekt)

---

### 12. Projektpreis festlegen

Als Nutzer/Ersteller möchte ich einen Preis für mein Projekt festlegen.
Beschreibung: Die Anwendung ermöglicht die Monetarisierung von Projekten.
Input: Projekt-ID, Preis
Output: Preis gespeichert (intern: Preisdaten)


### Use Case 



### Data types 

### Inputs and expected outputs
