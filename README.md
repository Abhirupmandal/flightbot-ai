# AeroScheduler — Airline Scheduling & Cargo Schedules Expert System

A **rule-based Expert System** built with Python Flask that validates and optimizes airline flight schedules and cargo shipments using **forward-chaining inference**. Designed as a capstone project demonstrating AI concepts including knowledge representation, inference engines, and decision-making.

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Features](#features)
4. [Tech Stack](#tech-stack)
5. [Installation & Setup](#installation--setup)
6. [Running the Application](#running-the-application)
7. [Running Tests](#running-tests)
8. [Project Structure](#project-structure)
9. [Knowledge Base](#knowledge-base)
10. [Expert Rules](#expert-rules)
11. [API Reference](#api-reference)
12. [Screenshots](#screenshots)

---

## Overview

AeroScheduler is an expert system that applies **15 expert rules** across three categories (flight, crew, and cargo) to validate scheduling decisions. It uses a **forward-chaining inference engine** — the engine iterates through all rules, fires those whose conditions match the input facts, and produces validation results, warnings, and recommendations.

### Key Concepts

| Concept | Implementation |
|---------|---------------|
| **Knowledge Base** | Static facts about 6 aircraft, 8 airports, 19 routes, 6 cargo types, and scheduling parameters |
| **Inference Engine** | Forward-chaining evaluator that applies all 15 rules to input data |
| **Rule Format** | IF (condition) THEN (action) with severity levels |
| **Conflict Detection** | Aircraft double-booking and gate conflict detection |
| **Recommendations** | Optimal aircraft suggestions, fuel efficiency, handling notes |

---

## System Architecture

```
┌─────────────────────────────────────────────────┐
│                  User Interface                  │
│         (Flask + Jinja2 Templates + JS)          │
├─────────────────────────────────────────────────┤
│                 Flask Application                │
│     Routes, Auth, Export, API Endpoints          │
├──────────────────┬──────────────────────────────┤
│  Inference Engine │     SQLite Database          │
│  (Forward Chain)  │  (Users, Flights, Cargo)     │
├──────────────────┴──────────────────────────────┤
│              Knowledge Base                      │
│  Aircraft Fleet | Airports | Routes | Rules      │
│  Cargo Types | Scheduling Parameters             │
└─────────────────────────────────────────────────┘
```

**Data Flow:**
1. User submits a flight or cargo schedule via the web form
2. Flask receives the request and passes data to the Inference Engine
3. The engine evaluates all applicable rules using forward chaining
4. Results (approve/warn/reject) are returned with explanations
5. The record is persisted to the SQLite database
6. The UI displays validation results and recommendations

---

## Features

### Core Expert System
- **Forward-chaining inference engine** with 15 expert rules
- **Flight scheduling** with validation against range, curfews, crew limits, turnaround times
- **Cargo scheduling** with validation against weight/volume, hazmat, perishables, live animals
- **Conflict detection** (aircraft double-booking, gate conflicts)
- **Smart recommendations** (optimal aircraft, fuel estimates, handling notes)

### Database Persistence (SQLite)
- All flights and cargo shipments are persisted to a SQLite database
- Data survives server restarts
- Uses SQLAlchemy ORM with proper models and relationships

### User Authentication
- User registration with validation (unique username/email, password strength)
- Login/logout with Flask-Login session management
- Protected routes — all scheduling pages require authentication
- Password hashing with Werkzeug

### Analytics & Data Visualization
- Interactive charts powered by Chart.js
- Flight status distribution (doughnut chart)
- Cargo status distribution (doughnut chart)
- Aircraft usage (bar chart)
- Route distribution (bar chart)
- Cargo type breakdown (pie chart)
- Summary statistics grid

### Export Functionality
- Export flights as **CSV** or **PDF**
- Export cargo shipments as **CSV** or **PDF**
- PDF reports generated with ReportLab with styled tables
- Export buttons available on individual pages and the analytics page

### Unit Testing
- **89 tests** across 4 test modules using pytest
- Tests cover: knowledge base integrity, inference engine rules, schedulers, Flask routes, auth, API, exports, database persistence

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3, Flask 3.1 |
| **Database** | SQLite via Flask-SQLAlchemy |
| **Auth** | Flask-Login + Werkzeug password hashing |
| **Charts** | Chart.js 4.x (CDN) |
| **PDF Export** | ReportLab |
| **Testing** | pytest |
| **Frontend** | HTML5, CSS3, vanilla JavaScript |

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/Abhirupmandal/flightbot-ai.git
cd flightbot-ai

# 2. (Recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Running the Application

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

On first launch:
1. You'll be redirected to the **login page**
2. Click **"Register here"** to create an account
3. After registration, you'll be logged in automatically
4. Start scheduling flights and cargo!

---

## Running Tests

```bash
# Run all tests with verbose output
python -m pytest tests/ -v

# Run a specific test module
python -m pytest tests/test_inference_engine.py -v

# Run with coverage (install pytest-cov first)
pip install pytest-cov
python -m pytest tests/ --cov=expert_system --cov=app --cov-report=term-missing
```

**Test modules:**
| Module | Tests | What it covers |
|--------|-------|---------------|
| `test_knowledge_base.py` | 18 | Aircraft, airports, routes, cargo types, rules data integrity |
| `test_inference_engine.py` | 16 | Flight & cargo rule evaluation, recommendations |
| `test_schedulers.py` | 17 | Flight & cargo scheduler logic, conflicts, summaries |
| `test_app.py` | 38 | Flask routes, auth, API, exports, DB persistence |

---

## Project Structure

```
flightbot-ai/
├── app.py                              # Flask application (routes, auth, API, export)
├── requirements.txt                    # Python dependencies
├── README.md                           # This file
│
├── expert_system/                      # Core expert system modules
│   ├── __init__.py
│   ├── knowledge_base.py              # Facts: aircraft, airports, routes, rules
│   ├── inference_engine.py            # Forward-chaining rule evaluator
│   ├── flight_scheduler.py            # Flight scheduling & conflict detection
│   ├── cargo_scheduler.py             # Cargo scheduling & optimization
│   └── models.py                      # SQLAlchemy models (User, Flight, Cargo)
│
├── templates/                          # Jinja2 HTML templates
│   ├── base.html                      # Base layout with sidebar nav
│   ├── login.html                     # Login page
│   ├── register.html                  # Registration page
│   ├── index.html                     # Dashboard
│   ├── flights.html                   # Flight scheduling form + table
│   ├── cargo.html                     # Cargo scheduling form + table
│   ├── analytics.html                 # Charts & export page
│   └── knowledge.html                 # Knowledge base reference tables
│
├── static/
│   ├── css/style.css                  # All styles
│   └── js/main.js                     # Client-side JavaScript
│
├── tests/                              # pytest test suite
│   ├── __init__.py
│   ├── test_knowledge_base.py         # Knowledge base data tests
│   ├── test_inference_engine.py       # Inference engine rule tests
│   ├── test_schedulers.py            # Scheduler logic tests
│   └── test_app.py                    # Flask route & integration tests
│
└── instance/
    └── aeroscheduler.db               # SQLite database (auto-created)
```

---

## Knowledge Base

### Aircraft Fleet (6 aircraft)

| Code | Type | Category | Range (km) | Passengers | Cargo (kg) |
|------|------|----------|-----------|------------|-----------|
| B737-800 | Boeing 737-800 | Narrow-body | 5,765 | 189 | 5,500 |
| A320neo | Airbus A320neo | Narrow-body | 6,300 | 194 | 6,000 |
| B777-300ER | Boeing 777-300ER | Wide-body | 13,650 | 396 | 23,000 |
| A350-900 | Airbus A350-900 | Wide-body | 15,000 | 325 | 20,000 |
| B747-400F | Boeing 747-400F | Freighter | 8,230 | 0 | 112,760 |
| A330-200F | Airbus A330-200F | Freighter | 7,400 | 0 | 70,000 |

### Airports (8 airports)

JFK, LAX, LHR, DXB, SIN, HKG, FRA, ORD — all with cargo facilities, peak hours, and curfew data.

### Cargo Types (6 types)

General, Perishable, Hazardous, Live Animals, Valuable, Oversized — each with priority, transit limits, and handling requirements.

---

## Expert Rules

| ID | Name | Category | Severity | What It Checks |
|----|------|----------|----------|---------------|
| R01 | Aircraft Range Check | Flight | Critical | Route distance vs. aircraft max range |
| R02 | Turnaround Time Check | Flight | High | Min turnaround by aircraft category |
| R03 | Night Curfew Check | Flight | Critical | Departure/arrival during airport curfew |
| R04 | Crew Duty Hours | Crew | Critical | Max 14 hrs duty per day |
| R05 | Crew Rest Requirement | Crew | Critical | Min 10 hrs rest between duties |
| R06 | Cargo Weight Limit | Cargo | Critical | Cargo weight vs. aircraft capacity |
| R07 | Cargo Volume Limit | Cargo | Critical | Cargo volume vs. aircraft hold |
| R08 | Hazardous Cargo Limit | Cargo | Critical | Max 500 kg hazmat per flight |
| R09 | Perishable Transit Time | Cargo | High | Max transit hours for perishables |
| R10 | Live Animal Transit | Cargo | Critical | Max 18 hrs for live animals |
| R11 | Peak Hour Buffer | Flight | Medium | 15-min buffer during peak hours |
| R12 | Cargo Facility Check | Cargo | Critical | Airport must have cargo facility |
| R13 | Hazmat-Passenger Separation | Cargo | High | Warning for hazmat on passenger flights |
| R14 | Freighter Recommendation | Cargo | Info | Suggests freighter for heavy cargo |
| R15 | Connection Time Check | Flight | Critical | Min 60-min connection time |

---

## API Reference

All API endpoints require authentication.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/flights` | Schedule a new flight (JSON body) |
| `POST` | `/api/flights/<id>/delete` | Delete a flight |
| `POST` | `/api/cargo` | Schedule a new cargo shipment (JSON body) |
| `POST` | `/api/cargo/<id>/delete` | Delete a cargo shipment |
| `GET` | `/api/summary` | Get full schedule summary |
| `GET` | `/api/conflicts` | Get detected conflicts |
| `GET` | `/api/chart-data` | Get analytics chart data |
| `GET` | `/export/flights/csv` | Download flights as CSV |
| `GET` | `/export/flights/pdf` | Download flights as PDF |
| `GET` | `/export/cargo/csv` | Download cargo as CSV |
| `GET` | `/export/cargo/pdf` | Download cargo as PDF |

### Example: Schedule a Flight

```bash
curl -X POST http://localhost:5000/api/flights \
  -H "Content-Type: application/json" \
  -d '{
    "flight_number": "AS-101",
    "aircraft": "B777-300ER",
    "origin": "JFK",
    "destination": "LHR",
    "departure_time": "10:00",
    "arrival_time": "22:00"
  }'
```

---

## Screenshots

### Dashboard
The dashboard shows an overview of all scheduled flights and cargo, with status cards, conflict alerts, and expert rules summary.

### Flight Scheduling
Interactive form to schedule flights with real-time validation through the inference engine. Results show rule-by-rule evaluation with severity indicators.

### Cargo Scheduling
Form to schedule cargo shipments with automatic transit time estimation, weight/volume utilization tracking, and hazmat validation.

### Analytics
Interactive Chart.js charts showing flight/cargo status distribution, aircraft usage, route distribution, and cargo type breakdown. Includes export buttons for CSV and PDF.

### Knowledge Base
Reference tables showing the complete knowledge base: aircraft fleet, airports, cargo types, all 15 expert rules, and scheduling parameters.

---

## License

This project was built as an academic capstone project demonstrating expert system concepts.
