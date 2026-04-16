# AeroScheduler - Airline Scheduling & Cargo Schedules Expert System

An expert system for airline flight scheduling and cargo schedule management built with Python and Flask. Uses a **rule-based inference engine** with **forward chaining** to validate schedules, detect conflicts, and generate optimization recommendations.

## Expert System Architecture

```
┌─────────────────────────┐
│     User Interface      │   Web-based forms for flight & cargo scheduling
│   (Flask + HTML/CSS)    │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│    Inference Engine      │   Forward-chaining rule evaluator
│  (15 Expert Rules)      │   Applies all matching rules to input facts
└───────┬─────────┬───────┘
        │         │
┌───────▼───┐ ┌───▼──────────┐
│ Knowledge │ │   Output     │
│   Base    │ │  Module      │
│           │ │              │
│ • Aircraft│ │ • Validation │
│ • Airports│ │ • Warnings   │
│ • Rules   │ │ • Recommend  │
│ • Cargo   │ │   -ations    │
└───────────┘ └──────────────┘
```

## Features

### Flight Scheduling
- Schedule flights with aircraft, route, and timing details
- **Rule-based validation**: aircraft range, night curfews, turnaround times, crew duty/rest hours
- Automatic conflict detection (aircraft double-booking, gate conflicts)
- Peak hour buffer warnings
- Connection time validation

### Cargo Scheduling
- Schedule cargo shipments with type, weight, and volume
- **6 cargo types**: General, Perishable, Hazardous, Live Animals, Valuable, Oversized
- Weight/volume capacity validation
- Hazardous material restrictions (IATA DGR compliance)
- Perishable and live animal transit time limits
- Cargo facility availability checks
- Cargo loading optimization

### Knowledge Base
- **6 aircraft types** (narrow-body, wide-body, freighter)
- **8 international airports** with curfews and peak hours
- **19 route distances**
- **15 expert rules** across flight, crew, and cargo categories
- Configurable scheduling parameters

### Inference Engine
- Forward-chaining rule evaluation
- Multi-severity findings: Critical, High, Medium, Info
- Smart recommendations (optimal aircraft, fuel efficiency, handling notes)
- Conflict detection between scheduled flights

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd airline-expert-system

# Create a virtual environment (optional)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The application will be available at `http://localhost:5000`.

## Pages

| Page | Description |
|------|-------------|
| **Dashboard** | Overview of flights, cargo, conflicts, and system status |
| **Flight Scheduling** | Add flights, validate against rules, view schedule |
| **Cargo Scheduling** | Add cargo shipments, validate, view utilization |
| **Knowledge Base** | View all aircraft, airports, cargo types, rules, and parameters |

## Expert Rules

| ID | Rule | Category | Severity |
|----|------|----------|----------|
| R01 | Aircraft Range Check | Flight | Critical |
| R02 | Turnaround Time Check | Flight | High |
| R03 | Night Curfew Check | Flight | Critical |
| R04 | Crew Duty Hours | Crew | Critical |
| R05 | Crew Rest Requirement | Crew | Critical |
| R06 | Cargo Weight Limit | Cargo | Critical |
| R07 | Cargo Volume Limit | Cargo | Critical |
| R08 | Hazardous Cargo Limit | Cargo | Critical |
| R09 | Perishable Transit Time | Cargo | High |
| R10 | Live Animal Transit | Cargo | Critical |
| R11 | Peak Hour Buffer | Flight | Medium |
| R12 | Cargo Facility Check | Cargo | Critical |
| R13 | Hazmat-Passenger Separation | Cargo | High |
| R14 | Freighter Recommendation | Cargo | Info |
| R15 | Connection Time Check | Flight | Critical |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/flights` | Add and validate a new flight |
| POST | `/api/flights/<id>/delete` | Delete a flight |
| POST | `/api/cargo` | Add and validate a cargo shipment |
| POST | `/api/cargo/<id>/delete` | Delete a shipment |
| GET | `/api/cargo/optimize/<aircraft>` | Get cargo loading optimization |
| GET | `/api/conflicts` | Get schedule conflicts |
| GET | `/api/summary` | Get full system summary |

## Technology Stack

- **Backend**: Python 3, Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Expert System**: Custom rule-based inference engine with forward chaining
- **Data**: In-memory knowledge base with aircraft, airport, and rule databases

## Project Structure

```
airline-expert-system/
├── app.py                          # Flask application & routes
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── expert_system/
│   ├── __init__.py
│   ├── knowledge_base.py           # Facts, rules, aircraft & airport data
│   ├── inference_engine.py         # Forward-chaining rule evaluator
│   ├── flight_scheduler.py         # Flight scheduling & validation
│   └── cargo_scheduler.py          # Cargo scheduling & optimization
├── templates/
│   ├── base.html                   # Base template with sidebar navigation
│   ├── index.html                  # Dashboard page
│   ├── flights.html                # Flight scheduling page
│   ├── cargo.html                  # Cargo scheduling page
│   └── knowledge.html              # Knowledge base viewer
└── static/
    ├── css/
    │   └── style.css               # Application styles
    └── js/
        └── main.js                 # Client-side JavaScript
```
