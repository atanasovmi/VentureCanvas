"""Idempotent demo-data seeder.

Seeds one demo user plus ~80 curated projects spread across the five
categories so the home page, category filter, search, sort, and
load-more all have meaningful data during demos. Counts deliberately
vary per category (Hardware gets the most, IoT the least) so the
seeded distribution feels organic rather than perfectly balanced.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Sequence, Tuple

from sqlmodel import Session, select

from ..domain.models import Category, Project, User
from .password_hasher import PasswordHasher


# Module-level constant so it's easy to scan and edit the seed content
# without touching the seeder mechanics. Entries are grouped by category
# and rendered newest-first within each section.
#
# Each entry is a dict with the same six keys, which map 1:1 onto the
# Project model: title, description, skills, tools, apis, hardware.
# (The "required_" prefix is added by the builder below.)
_SAMPLE_PROJECTS_BY_CATEGORY: dict[Category, list[dict]] = {
    # ── IoT · sensors & connected devices ──────────────────────────────
    Category.IOT: [
        dict(
            title="Smart Plant Watering",
            description=(
                "ESP32-based soil-moisture monitor that turns on a small "
                "pump when the plant is thirsty and logs readings to a "
                "cloud dashboard."
            ),
            skills="MicroPython, soldering, HTTP basics",
            tools="ESP32, breadboard, jumper wires",
            apis="ThingSpeak",
            hardware="Soil-moisture sensor, 5V pump, LiPo cell",
        ),
        dict(
            title="Air-Quality Map",
            description=(
                "A small network of PM2.5 sensors streaming readings to "
                "a shared dashboard so you can see pollution hotspots in "
                "your city."
            ),
            skills="MicroPython, MQTT, web charts",
            tools="ESP32, Mosquitto",
            apis="InfluxDB Cloud",
            hardware="PMS5003 sensor, OLED display",
        ),
        dict(
            title="Hive Pulse",
            description=(
                "Microphones inside a beehive stream audio features to a "
                "Pi; an ML classifier flags queenless or swarming "
                "colonies before the keeper opens the lid."
            ),
            skills="Python, signal processing, scikit-learn",
            tools="Raspberry Pi, Edge Impulse",
            apis="",
            hardware="USB lavalier mic, weatherproof enclosure",
        ),
        dict(
            title="Tide Watch",
            description="Solar-powered float that beams sea-level samples to a coastal LoRa gateway every five minutes.",
            skills="C++, low-power design",
            tools="STM32, RAK gateway",
            apis="TheThingsNetwork",
            hardware="Pressure transducer, LiFePO4 cell, 12V solar panel",
        ),
        dict(
            title="Lab Fridge Sentinel",
            description=(
                "Thermistor probe inside a -80°C freezer pings the lab "
                "Slack channel if the door stays open more than 30 seconds."
            ),
            skills="Embedded C, Slack webhook setup",
            tools="ESP8266, Arduino IDE",
            apis="Slack",
            hardware="Negative-temp thermistor probe, magnetic reed switch",
        ),
        dict(
            title="Greenhouse LoRa Mesh",
            description="Twelve-node mesh tracks soil moisture, light and temperature across a hobby greenhouse and surfaces dry beds.",
            skills="LoRaWAN basics, light electronics",
            tools="Heltec WiFi LoRa boards",
            apis="",
            hardware="DHT22, capacitive moisture probes, 3D-printed nodes",
        ),
        dict(
            title="Bike Theft Tracker",
            description=(
                "GPS + GSM beacon hidden in the seat-post that wakes on "
                "motion and SMSes its location to the owner."
            ),
            skills="Arduino C, GSM AT commands",
            tools="SIM7600 module, M5StickC",
            apis="",
            hardware="Discrete antenna, 1100 mAh LiPo, accelerometer",
        ),
        dict(
            title="Parking-Lot Counter",
            description=(
                "Battery-powered presence sensors mesh together to keep "
                "a live count of free spaces at a small office lot."
            ),
            skills="LoRa, low-power MCU programming",
            tools="Arduino MKR WAN 1310",
            apis="TheThingsNetwork",
            hardware="VL53L1X ToF sensors, IP67 enclosures",
        ),
        dict(
            title="Solar Inverter Logger",
            description="Reads Modbus from a string inverter and graphs daily yield against weather forecasts.",
            skills="Python, Modbus RTU",
            tools="Raspberry Pi Zero",
            apis="OpenWeather",
            hardware="USB-to-RS485 adapter",
        ),
        dict(
            title="Mailbox Notifier",
            description=(
                "Reed switch glued inside a physical mailbox sends a "
                "push notification the moment the postie drops anything in."
            ),
            skills="MicroPython, push notifications",
            tools="ESP32-C3, ntfy",
            apis="ntfy.sh",
            hardware="Reed switch, magnet, AAA pack",
        ),
    ],
    # ── AI · models, agents & RAG ──────────────────────────────────────
    Category.AI: [
        dict(
            title="Retrieval-Augmented Chatbot",
            description=(
                "A small RAG application that answers questions over a "
                "local PDF corpus using a vector store and a chat model."
            ),
            skills="Python, embeddings, prompt design",
            tools="LangChain, Chroma",
            apis="OpenAI",
            hardware="",
        ),
        dict(
            title="PaperGraph",
            description=(
                "Crawls citations across arXiv to build a navigable "
                "graph around any paper, with one-paragraph LLM "
                "summaries on each node."
            ),
            skills="Graph algorithms, Python",
            tools="NetworkX, FAISS",
            apis="arXiv, OpenAI",
            hardware="",
        ),
        dict(
            title="Whisper-to-Subtitles",
            description="Drop a video on this desktop app and find a polished .srt next to it 30 seconds later.",
            skills="Python, FFmpeg, Whisper",
            tools="PyQt6",
            apis="",
            hardware="",
        ),
        dict(
            title="RAG over Slack",
            description=(
                "Workspace-wide semantic search that answers 'has anyone "
                "ever solved X?' across years of Slack history."
            ),
            skills="Python, embeddings",
            tools="Chroma, FastAPI",
            apis="Slack, OpenAI",
            hardware="",
        ),
        dict(
            title="Resume Sniper",
            description="Paste a job description; the model rewrites your CV bullets so each requirement is addressed explicitly.",
            skills="Prompt engineering",
            tools="Next.js",
            apis="OpenAI",
            hardware="",
        ),
        dict(
            title="Lecture Note Distiller",
            description=(
                "Eats a recorded lecture and produces a structured study "
                "guide: headings, key terms, sample questions, references."
            ),
            skills="Audio pipelines, Python",
            tools="Whisper, pydantic",
            apis="OpenAI",
            hardware="",
        ),
        dict(
            title="Receipt OCR Wallet",
            description="Mobile-first PWA that snaps a receipt, parses the line items, and auto-tags spend categories.",
            skills="OCR, React",
            tools="Tesseract, Next.js",
            apis="",
            hardware="",
        ),
        dict(
            title="Image Caption Studio",
            description=(
                "Alt-text generator with a side-by-side correction UI so "
                "editors can keep tone consistent across thousands of images."
            ),
            skills="Vision-language models",
            tools="Streamlit, BLIP",
            apis="",
            hardware="",
        ),
        dict(
            title="Code Review Sidekick",
            description="GitHub Action that posts a 5-bullet summary of any pull request and flags risky diffs.",
            skills="Python, GitHub Actions",
            tools="PyGitHub",
            apis="GitHub, OpenAI",
            hardware="",
        ),
        dict(
            title="Plant Disease Diagnoser",
            description="Upload a leaf photo; a fine-tuned vision model returns the three most likely conditions with confidence.",
            skills="Computer vision, PyTorch",
            tools="FastAI, Gradio",
            apis="",
            hardware="",
        ),
        dict(
            title="Recipe Substitutor",
            description=(
                "'I'm out of buttermilk' — the model suggests viable "
                "swaps for any ingredient given what's actually in your kitchen."
            ),
            skills="Prompt design",
            tools="Streamlit",
            apis="OpenAI",
            hardware="",
        ),
        dict(
            title="Meeting Action-Item Extractor",
            description=(
                "Listens to a Zoom recording and produces a clean list "
                "of decisions, owners and due dates — paste-ready into Linear."
            ),
            skills="Audio, structured output",
            tools="Whisper, pydantic",
            apis="OpenAI",
            hardware="",
        ),
        dict(
            title="Diet Diary",
            description="Snap a meal; a vision model returns rough calorie and macro estimates with a 'log this' button.",
            skills="Vision models, React Native",
            tools="Expo",
            apis="OpenAI Vision",
            hardware="",
        ),
        dict(
            title="Voice Note Transcriber",
            description=(
                "Mac menu-bar app that turns iPhone voice memos into "
                "searchable text plus a one-line auto-summary."
            ),
            skills="Swift, async pipelines",
            tools="Whisper.cpp",
            apis="",
            hardware="",
        ),
        dict(
            title="Quote-Finder for Books",
            description="Type a half-remembered phrase; the model points to which book on your Calibre shelf actually contains it.",
            skills="Embeddings, ePub parsing",
            tools="FAISS, calibre-cli",
            apis="",
            hardware="",
        ),
        dict(
            title="Brand Tone Linter",
            description=(
                "Checks marketing drafts against a style guide and "
                "flags off-tone phrasing the way ESLint flags bad code."
            ),
            skills="NLP, rule design",
            tools="spaCy, Streamlit",
            apis="OpenAI",
            hardware="",
        ),
        dict(
            title="Personalized News Digest",
            description="Learns which headlines you actually open vs. skim and emails you a 5-minute morning brief.",
            skills="Recommender systems",
            tools="scikit-learn, Postmark",
            apis="NewsAPI",
            hardware="",
        ),
        dict(
            title="Smart Email Drafter",
            description=(
                "Reads the last 50 emails from a contact and drafts a "
                "reply in your voice — never sends, always preview."
            ),
            skills="Prompt design, IMAP",
            tools="Python, imapclient",
            apis="OpenAI",
            hardware="",
        ),
    ],
    # ── Web · apps that live in the browser ────────────────────────────
    Category.WEB: [
        dict(
            title="Collaborative Markdown Editor",
            description=(
                "Browser-based editor with live cursors and presence over "
                "WebSockets, built on a CRDT for conflict-free concurrent edits."
            ),
            skills="TypeScript, WebSockets, CRDTs",
            tools="Yjs, Vite",
            apis="",
            hardware="",
        ),
        dict(
            title="Cohort Scoreboard",
            description="Weekly auto-updating leaderboard for student cohorts; instructors point it at any spreadsheet of scores.",
            skills="TypeScript, React",
            tools="Next.js, Tailwind",
            apis="Google Sheets",
            hardware="",
        ),
        dict(
            title="Markdown Daily",
            description=(
                "Mails you a single journaling prompt every morning and "
                "archives your answers as a private git repo of dated .md files."
            ),
            skills="Python",
            tools="FastAPI, GitPython",
            apis="Postmark",
            hardware="",
        ),
        dict(
            title="Static Wiki for Teams",
            description="Git-backed wiki that compiles to static HTML — no database, no admin panel, PR review for every edit.",
            skills="Go, templating",
            tools="Hugo, GitHub Pages",
            apis="",
            hardware="",
        ),
        dict(
            title="Tiny URL with Analytics",
            description="A short-link service that exposes per-click country, referrer and device without leaking the visitor's identity.",
            skills="Rust, web fundamentals",
            tools="Axum, SQLite",
            apis="MaxMind GeoLite2",
            hardware="",
        ),
        dict(
            title="Pixel Letter Postcards",
            description=(
                "Draw a 64x64 pixel image in the browser and email it "
                "to a friend — they get a permalink and a print-ready PNG."
            ),
            skills="Canvas API, TypeScript",
            tools="SvelteKit",
            apis="Resend",
            hardware="",
        ),
        dict(
            title="Read-Later for RSS",
            description="Brings back the Google Reader workflow: minimalist 3-pane layout, keyboard navigation, instant unread sync.",
            skills="TypeScript",
            tools="SolidJS, Bun",
            apis="",
            hardware="",
        ),
        dict(
            title="Open Mic Map",
            description=(
                "Crowdsourced map of next week's spoken-word and "
                "open-mic events; venues claim their listings via magic-link email."
            ),
            skills="Full-stack TypeScript",
            tools="Remix, PostGIS",
            apis="Mapbox",
            hardware="",
        ),
        dict(
            title="Sketch-to-Site",
            description="Upload a phone photo of a paper wireframe and the model returns a clean Tailwind HTML scaffold.",
            skills="Computer vision, Tailwind",
            tools="Next.js",
            apis="OpenAI",
            hardware="",
        ),
        dict(
            title="Pomodoro Office",
            description="Shared timer rooms — your remote pair sees the same red bar countdown. No chat, no video, just rhythm.",
            skills="WebRTC, TypeScript",
            tools="Cloudflare Durable Objects",
            apis="",
            hardware="",
        ),
        dict(
            title="Async Standup Bot",
            description=(
                "Slack bot that DMs each team member a 3-question "
                "standup at 9am and threads the answers in #standup by 10."
            ),
            skills="Python, Slack APIs",
            tools="FastAPI, Bolt",
            apis="Slack",
            hardware="",
        ),
        dict(
            title="Studio Booking Board",
            description="Small recording studios accept slot bookings and sync them straight into the engineer's iCal.",
            skills="TypeScript, calendar formats",
            tools="Remix, ical.js",
            apis="Google Calendar",
            hardware="",
        ),
        dict(
            title="Hackathon Team Matcher",
            description=(
                "Submit your skills and interests 24h before kickoff; "
                "the app proposes a balanced team and a Slack channel template."
            ),
            skills="Matching algorithms",
            tools="Next.js, Postgres",
            apis="Slack",
            hardware="",
        ),
        dict(
            title="Library Reading Group",
            description="Tiny app where 6-person book clubs vote on the next title and check off chapter-by-chapter progress.",
            skills="Vue, simple voting logic",
            tools="Nuxt, SQLite",
            apis="OpenLibrary",
            hardware="",
        ),
        dict(
            title="Code Snippet Pastebin",
            description=(
                "Syntax-highlighted pastes that expire on first view — "
                "designed for sharing one-off secrets you can't put in Slack."
            ),
            skills="Rust, web fundamentals",
            tools="Axum, Tera",
            apis="",
            hardware="",
        ),
        dict(
            title="Garage Sale Locator",
            description="Neighbours drop pins on a shared map for the weekend's garage sales, with photos and rough categories.",
            skills="Full-stack JS, maps",
            tools="SvelteKit, Leaflet",
            apis="OpenStreetMap",
            hardware="",
        ),
        dict(
            title="Recipe Sharing Forum",
            description=(
                "Old-school threaded forum specifically for home cooks — "
                "no ads, no SEO walls, just recipes and the people who "
                "tweak them."
            ),
            skills="Rails, Markdown",
            tools="Ruby on Rails",
            apis="",
            hardware="",
        ),
    ],
    # ── Mobile · iOS & Android builds ──────────────────────────────────
    Category.MOBILE: [
        dict(
            title="Habit Tracker",
            description=(
                "Offline-first mobile app that tracks daily habits, "
                "keeps streak counts, and sends gentle reminders."
            ),
            skills="Flutter, Dart",
            tools="Flutter SDK, Android Studio",
            apis="",
            hardware="",
        ),
        dict(
            title="Trail Companion",
            description="Offline GPS hike tracker that overlays elevation, breaks and water-source pins on a downloadable map.",
            skills="Kotlin, Android",
            tools="Android Studio",
            apis="OpenStreetMap",
            hardware="",
        ),
        dict(
            title="Insulin Log",
            description=(
                "Two-tap blood-glucose and dose entry with a monthly "
                "PDF export your endocrinologist will actually open."
            ),
            skills="Swift, SwiftUI",
            tools="Xcode",
            apis="HealthKit",
            hardware="",
        ),
        dict(
            title="Pocket Stargazer",
            description="Point your phone at the sky and the app names the brightest object plus the constellation it belongs to.",
            skills="AR, ARKit",
            tools="RealityKit",
            apis="Stellarium",
            hardware="",
        ),
        dict(
            title="Transit Predictor",
            description=(
                "Learns your typical commute and surfaces only the delays "
                "or platform changes that actually affect your route."
            ),
            skills="React Native, ML basics",
            tools="Expo",
            apis="GTFS-realtime",
            hardware="",
        ),
        dict(
            title="Tide & Sunrise Planner",
            description="One-tap surf, photography and fishing window finder for any beach you've saved.",
            skills="Flutter",
            tools="Flutter SDK",
            apis="NOAA Tides, Sunrise-Sunset",
            hardware="",
        ),
        dict(
            title="Field Botanist's Companion",
            description=(
                "Snap a flower, get a confidence-ranked ID and a private "
                "journal of every plant you've logged with GPS pins."
            ),
            skills="Mobile ML, Swift",
            tools="Core ML",
            apis="iNaturalist",
            hardware="",
        ),
        dict(
            title="Vinyl Spinner",
            description="Glue an NFC sticker to a record sleeve; tapping it on your phone pulls up the tracklist, notes and credits.",
            skills="Android, NFC",
            tools="Android Studio",
            apis="Discogs",
            hardware="",
        ),
        dict(
            title="Tea Brew Timer",
            description="Opens straight to a timer for your favourite tea; long-press the cup icon to switch leaf, swipe for water temp.",
            skills="SwiftUI",
            tools="Xcode",
            apis="",
            hardware="",
        ),
        dict(
            title="Bird Call Identifier",
            description=(
                "Record five seconds of birdsong on a walk and an "
                "on-device model returns a confidence-ranked species ID."
            ),
            skills="Mobile ML, Kotlin",
            tools="TensorFlow Lite",
            apis="",
            hardware="",
        ),
        dict(
            title="Quiet Hours",
            description="Phone silences itself automatically when you arrive at marked locations (your dentist, your in-laws, your meditation studio).",
            skills="Android, geofencing",
            tools="Android Studio",
            apis="",
            hardware="",
        ),
        dict(
            title="Hand-Drawn Map Annotator",
            description=(
                "Take a photo of a paper hiking map; pin notes, photos "
                "and waypoints directly onto the image and share the bundle."
            ),
            skills="iOS, Core Image",
            tools="Xcode",
            apis="",
            hardware="",
        ),
        dict(
            title="No-Ads Period Tracker",
            description="Local-only cycle tracker — no account, no sync, no analytics. Ships an encrypted backup file you control.",
            skills="Flutter, encryption",
            tools="Flutter SDK",
            apis="",
            hardware="",
        ),
        dict(
            title="Garage Door BLE Remote",
            description=(
                "Replaces the dollar-store fob with a phone-paired BLE "
                "module — also lets you grant temporary access to a guest."
            ),
            skills="React Native, BLE",
            tools="Expo, react-native-ble-plx",
            apis="",
            hardware="",
        ),
    ],
    # ── Hardware · PCBs, robotics & physical builds ────────────────────
    Category.HARDWARE: [
        dict(
            title="DIY Mechanical Keyboard",
            description=(
                "A hand-soldered 40% split keyboard running QMK "
                "firmware with per-key RGB."
            ),
            skills="Soldering, C",
            tools="QMK, soldering iron, flux",
            apis="",
            hardware="Pro Micro, keycaps, switches, plate",
        ),
        dict(
            title="Pomodoro Cube",
            description="A six-faced timer cube — flip it on its side to start a 25/5/15 minute interval; E-ink face shows what's running.",
            skills="Embedded C++, low-power design",
            tools="PlatformIO",
            apis="",
            hardware='MPU6050, 1.54" E-ink, CR2032 holder',
        ),
        dict(
            title="Solar-tracked Camera Mount",
            description=(
                "Two-axis tracker that keeps a camera pointed at the sun "
                "for sharp eclipse and time-lapse footage."
            ),
            skills="Stepper drivers, CAD",
            tools="Fusion 360, Arduino IDE",
            apis="",
            hardware="NEMA17 steppers, A4988 drivers, ball head",
        ),
        dict(
            title="Cyberdeck Build",
            description=(
                "Pi 5 in a 3D-printed Pelican-style case with a 7-inch "
                "touchscreen, mechanical 65% layout, and rugged latches."
            ),
            skills="CAD, electronics integration",
            tools="Fusion 360, Bambu X1C",
            apis="",
            hardware='Pi 5, 7" HDMI panel, 18650 cells, BMS',
        ),
        dict(
            title="E-ink Calendar Frame",
            description='A wall-mounted 13.3" e-ink display that pulls your day from CalDAV and refreshes once an hour over WiFi.',
            skills="Python, low-power design",
            tools="Waveshare driver board",
            apis="CalDAV",
            hardware='13.3" e-ink panel, ESP32, picture frame',
        ),
        dict(
            title="Macro-pad Stream Controller",
            description=(
                "Twelve mechanical keys, each with its own OLED screen — "
                "icons change to match whatever app currently has focus."
            ),
            skills="Embedded C++, OLED multiplexing",
            tools="QMK fork, KiCad",
            apis="",
            hardware="MX switches, SSD1306 OLEDs, RP2040",
        ),
        dict(
            title="Filament Drybox",
            description=(
                "Heated chamber that keeps 3D-printer filament below 15% "
                "RH and logs humidity to a tiny OLED on the lid."
            ),
            skills="Embedded C",
            tools="PlatformIO",
            apis="",
            hardware="PTC heater, SHT31, food-safe gasket",
        ),
        dict(
            title="Word Clock",
            description=(
                "Wall clock that spells out the time in words via an "
                "11x11 LED matrix behind a laser-cut wood face."
            ),
            skills="LED matrix driving, woodworking",
            tools="ESP32, FastLED",
            apis="",
            hardware="WS2812B strip, laser-cut walnut face, RTC module",
        ),
        dict(
            title="Light-Painting Wand",
            description="Programmable RGB stick for long-exposure photography — load any PNG and walk it across the frame.",
            skills="Embedded C, image decoding",
            tools="Teensy 4.1",
            apis="",
            hardware="APA102 strip, 18650 grip, SD card slot",
        ),
        dict(
            title="Robotic Cocktail Shaker",
            description=(
                "Peristaltic-pump rig with a touchscreen that dispenses "
                "calibrated pours from up to eight bottles, then shakes "
                "via servo."
            ),
            skills="Mechatronics, food-safe design",
            tools="Raspberry Pi, FreeCAD",
            apis="",
            hardware="8x peristaltic pumps, 5\" HDMI touch, servo arm",
        ),
        dict(
            title="Open-Source Smart Lock",
            description="Fingerprint + BLE alternative for a standard front door, designed to swap in without changing the strike plate.",
            skills="CAD, embedded security",
            tools="Fusion 360, ESP32-S3",
            apis="",
            hardware="R503 fingerprint module, geared motor, latch cam",
        ),
        dict(
            title="Vintage Radio Bluetooth Conversion",
            description=(
                "Keep the brass dial and warm speaker of a 1960s tube "
                "radio; add a hidden Bluetooth board so phones stream "
                "through it."
            ),
            skills="Vintage electronics, audio",
            tools="Soldering iron, signal generator",
            apis="",
            hardware="Bluetooth audio module, 12V regulator, RCA pigtail",
        ),
        dict(
            title="Custom Game Boy Cartridge",
            description="Reflashable cartridge PCB for the original DMG-01, with switchable banks for hobby ROMs you've written yourself.",
            skills="Z80 assembly basics, PCB design",
            tools="KiCad, JLCPCB",
            apis="",
            hardware="29F033C flash chip, custom 2-layer PCB",
        ),
        dict(
            title="Auto-Color RGB Desk Lamp",
            description=(
                "Lamp that samples the dominant colour from your monitor "
                "and tints the wall behind it — pure ambient build, no "
                "screen capture in software."
            ),
            skills="Optics, embedded C",
            tools="Teensy, photoresistors",
            apis="",
            hardware="WS2812B ring, frosted diffuser, RGB sensor",
        ),
        dict(
            title="Mechanical Flip Calendar",
            description="Gear-driven date flip board that turns the page exactly at midnight using a stepper and a tiny RTC.",
            skills="3D printing, gears",
            tools="Fusion 360, Bambu X1C",
            apis="",
            hardware="NEMA8 stepper, DS3231 RTC, printed gears",
        ),
        dict(
            title="DIY Pen Plotter",
            description=(
                "A4 pen plotter assembled from two scrapped CD-ROM "
                "drives, a servo pen lift, and GRBL firmware."
            ),
            skills="GRBL, mechanical fabrication",
            tools="Arduino UNO, CNC shield",
            apis="",
            hardware="CD-ROM stepper rails, servo, fountain pen",
        ),
        dict(
            title="Sound-Reactive Window Decal",
            description="Translucent LED strip sandwiched between two layers of window film; pulses to ambient sound for parties.",
            skills="Electronics, materials",
            tools="ESP32, MEMS mic",
            apis="",
            hardware="WS2812B strip, dichroic film, double-sided window mount",
        ),
        dict(
            title="Pi Thin Client Combo",
            description=(
                "Pi Zero 2 W glued to the back of a mechanical keyboard; "
                "boots straight into an RDP session over WiFi, ideal for "
                "kiosk-style remote work."
            ),
            skills="Linux, kiosk setup",
            tools="Raspberry Pi, freerdp",
            apis="",
            hardware="Pi Zero 2 W, USB-C splitter, 3D-printed mount",
        ),
        dict(
            title="Programmable Camera Slider",
            description=(
                "One-metre motorised rail with G-code-style scripting "
                "for eased motion — perfect for product time-lapses."
            ),
            skills="Stepper control, mechanical design",
            tools="Marlin fork, aluminium extrusion",
            apis="",
            hardware="NEMA17, 1m linear rail, GT2 belt, controller",
        ),
        dict(
            title="Desk Weather Cube",
            description=(
                "4cm desk cube with an E-ink face cycling between "
                "temperature, humidity and pressure once a minute."
            ),
            skills="Embedded C, low-power design",
            tools="STM32L0, PlatformIO",
            apis="",
            hardware='BME280, 1.54" E-ink, CR2032 holder',
        ),
        dict(
            title="Mechanical Keyboard Stand",
            description="Adjustable walnut riser with built-in cable channels and a hidden palm-rest drawer.",
            skills="Woodworking, basic CAD",
            tools="Fusion 360, table saw",
            apis="",
            hardware="Walnut block, brass hinge, rubber feet",
        ),
        dict(
            title="USB Volume Knob",
            description=(
                "One big anodised aluminium knob over an encoder; "
                "appears as a USB HID consumer-control device — turn for "
                "volume, click to mute."
            ),
            skills="USB HID, machining",
            tools="Pro Micro, Arduino IDE",
            apis="",
            hardware="Aluminium knob, EC11 encoder, 3D-printed base",
        ),
    ],
}


class ProjectSeeder:
    """Seeds the demo user plus ~80 sample projects.

    Instantiated by the composition root with a
    :class:`PasswordHasher`, so the demo user's password is hashed with
    exactly the same routine as every live registration. Idempotent on
    the demo user — delete the SQLite file to re-seed during dev.
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
        # Stagger timestamps so Newest/Oldest/A-Z sorts each produce a
        # different visible order — important for demoing the sort dropdown.
        now = datetime.now(timezone.utc)
        # Flatten the {category: [entries]} map into one ordered list of
        # (category, entry) pairs so we can assign each a distinct timestamp.
        flat: List[Tuple[Category, dict]] = [
            (cat, item)
            for cat, items in _SAMPLE_PROJECTS_BY_CATEGORY.items()
            for item in items
        ]
        projects: List[Project] = []
        for i, (cat, item) in enumerate(flat):
            # Each project is one day + a few hours older than the previous,
            # giving every row a unique created_at for stable sorting.
            ts = now - timedelta(days=i, hours=(i * 7) % 24)
            projects.append(
                Project(
                    owner_id=owner_id,
                    title=item["title"],
                    description=item["description"],
                    category=cat,
                    required_skills=item["skills"],
                    required_tools=item["tools"],
                    required_apis=item["apis"],
                    required_hardware=item["hardware"],
                    created_at=ts,
                    updated_at=ts,
                )
            )
        return projects
