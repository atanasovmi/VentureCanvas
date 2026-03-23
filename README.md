# VentureCanvas
## Project description 
Eine community-getriebene Plattform für Innovationsprojekte

Diese Webplattform dient als zentraler Ort, an dem Nutzer ihre innovativen Projekte präsentieren, entdecken und weiterentwickeln können. 
 
Nutzer haben die Möglichkeit, eigene Projekte hochzuladen und detailliert vorzustellen, inklusive Beschreibungen, Dateien und weiterführenden Informationen. Gleichzeitig können sie durch Projekte anderer stöbern, sich inspirieren lassen.
 
Ein zentraler Bestandteil der Plattform ist die Interaktion innerhalb der Community: Projekte können kommentiert, diskutiert und bewertet werden. 
Nutzer können Projekte oder dazugehörige Dateien kaufen und herunterladen, um diese weiterzuverwenden oder als Grundlage für eigene Entwicklungen zu nutzen.
Insgesamt verbindet die Plattform Präsentation, Zusammenarbeit und Monetarisierung.

 <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white" alt="Python"> <img src="https://img.shields.io/badge/Flask-3.1-black?logo=flask&logoColor=white" alt="Flask"> <img src="https://img.shields.io/badge/Vue-3-4FC08D?logo=vue.js&logoColor=white" alt="Vue 3"> <img src="https://img.shields.io/badge/Quasar-2-1976D2?logo=quasar&logoColor=white" alt="Quasar"> <img src="https://img.shields.io/badge/SQLAlchemy-2.0-red?logo=python&logoColor=white" alt="SQLAlchemy"> <img src="https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white" alt="TypeScript"> <img src="https://img.shields.io/badge/License-MIT-green" alt="License">

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
