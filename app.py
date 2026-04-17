"""
AeroScheduler Expert System - Main Flask Application

An expert system for airline flight scheduling and cargo schedule management.
Uses a rule-based inference engine with forward chaining to validate schedules,
detect conflicts, and generate optimization recommendations.

Enhanced with: SQLite persistence, user authentication, data visualization,
and export capabilities.
"""

import csv
import io
import json
import os
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, jsonify, redirect,
    url_for, flash, Response, make_response,
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user,
)

from expert_system.models import db, User, FlightRecord, CargoRecord
from expert_system.knowledge_base import (
    AIRCRAFT_FLEET,
    AIRPORTS,
    CARGO_TYPES,
    EXPERT_RULES,
    SCHEDULING_RULES,
    get_route_distance,
)
from expert_system.flight_scheduler import FlightScheduler
from expert_system.cargo_scheduler import CargoScheduler

# ── App Setup ────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "aero-scheduler-dev-key-change-in-prod")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///aeroscheduler.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Create tables on startup
with app.app_context():
    db.create_all()


# ── Helpers ──────────────────────────────────────────────────────────────────

def _check_conflicts_from_db():
    """Build a local FlightScheduler from DB records and check conflicts.

    Uses a request-local instance to avoid race conditions and memory leaks.
    """
    from expert_system.flight_scheduler import Flight
    local_scheduler = FlightScheduler()
    for f in FlightRecord.query.all():
        fl = Flight.__new__(Flight)
        fl.id = f.id
        fl.flight_number = f.flight_number
        fl.aircraft = f.aircraft
        fl.origin = f.origin
        fl.destination = f.destination
        fl.departure_time = f.departure_time
        fl.arrival_time = f.arrival_time
        fl.status = f.status
        fl.validation_results = []
        local_scheduler.flights.append(fl)
    return local_scheduler.check_conflicts()


def _flight_record_to_dict(rec):
    """Convert a FlightRecord to a display dict (mirrors Flight.to_dict)."""
    aircraft_info = AIRCRAFT_FLEET.get(rec.aircraft, {})
    distance = get_route_distance(rec.origin, rec.destination)
    return {
        "id": rec.id,
        "flight_number": rec.flight_number,
        "aircraft": rec.aircraft,
        "aircraft_type": aircraft_info.get("type", "Unknown"),
        "origin": rec.origin,
        "origin_name": AIRPORTS.get(rec.origin, {}).get("name", "Unknown"),
        "destination": rec.destination,
        "destination_name": AIRPORTS.get(rec.destination, {}).get("name", "Unknown"),
        "departure_time": rec.departure_time,
        "arrival_time": rec.arrival_time,
        "distance_km": distance,
        "turnaround_time_min": rec.turnaround_time_min,
        "crew_duty_hours": rec.crew_duty_hours,
        "crew_rest_hours": rec.crew_rest_hours,
        "connection_time_min": rec.connection_time_min,
        "status": rec.status,
        "validation_results": json.loads(rec.validation_json),
        "created_at": rec.created_at.strftime("%Y-%m-%d %H:%M") if rec.created_at else "",
    }


def _cargo_record_to_dict(rec):
    """Convert a CargoRecord to a display dict (mirrors CargoShipment.to_dict)."""
    cargo_info = CARGO_TYPES.get(rec.cargo_type, {})
    aircraft_info = AIRCRAFT_FLEET.get(rec.aircraft, {})
    distance = get_route_distance(rec.origin, rec.destination)
    capacity_kg = aircraft_info.get("cargo_capacity_kg", 0)
    utilization = (rec.weight_kg / capacity_kg * 100) if capacity_kg else 0
    return {
        "id": rec.id,
        "shipment_number": rec.shipment_number,
        "aircraft": rec.aircraft,
        "aircraft_type": aircraft_info.get("type", "Unknown"),
        "origin": rec.origin,
        "origin_name": AIRPORTS.get(rec.origin, {}).get("name", "Unknown"),
        "destination": rec.destination,
        "destination_name": AIRPORTS.get(rec.destination, {}).get("name", "Unknown"),
        "cargo_type": rec.cargo_type,
        "cargo_type_name": cargo_info.get("name", "Unknown"),
        "weight_kg": rec.weight_kg,
        "volume_m3": rec.volume_m3,
        "is_passenger_flight": rec.is_passenger_flight,
        "estimated_transit_hours": rec.estimated_transit_hours,
        "description": rec.description,
        "distance_km": distance,
        "cargo_utilization_pct": round(utilization, 1),
        "priority": cargo_info.get("priority", 5),
        "handling_time_min": cargo_info.get("handling_time_min", 30),
        "status": rec.status,
        "validation_results": json.loads(rec.validation_json),
        "created_at": rec.created_at.strftime("%Y-%m-%d %H:%M") if rec.created_at else "",
    }


def _get_flight_summary():
    """Build flight summary from database."""
    flights = FlightRecord.query.all()
    total = len(flights)
    approved = sum(1 for f in flights if f.status == "approved")
    warning = sum(1 for f in flights if f.status == "warning")
    rejected = sum(1 for f in flights if f.status == "rejected")

    aircraft_usage = {}
    for f in flights:
        aircraft_usage.setdefault(f.aircraft, 0)
        aircraft_usage[f.aircraft] += 1

    route_counts = {}
    for f in flights:
        route = f"{f.origin}-{f.destination}"
        route_counts.setdefault(route, 0)
        route_counts[route] += 1

    return {
        "total_flights": total,
        "approved": approved,
        "warnings": warning,
        "rejected": rejected,
        "aircraft_usage": aircraft_usage,
        "route_counts": route_counts,
    }


def _get_cargo_summary():
    """Build cargo summary from database."""
    shipments = CargoRecord.query.all()
    total = len(shipments)
    approved = sum(1 for s in shipments if s.status == "approved")
    warning = sum(1 for s in shipments if s.status == "warning")
    rejected = sum(1 for s in shipments if s.status == "rejected")
    total_weight = sum(s.weight_kg for s in shipments)
    total_volume = sum(s.volume_m3 for s in shipments)

    type_breakdown = {}
    for s in shipments:
        cargo_info = CARGO_TYPES.get(s.cargo_type, {})
        name = cargo_info.get("name", s.cargo_type)
        type_breakdown.setdefault(name, {"count": 0, "weight": 0})
        type_breakdown[name]["count"] += 1
        type_breakdown[name]["weight"] += s.weight_kg

    route_breakdown = {}
    for s in shipments:
        route = f"{s.origin}-{s.destination}"
        route_breakdown.setdefault(route, {"count": 0, "weight": 0})
        route_breakdown[route]["count"] += 1
        route_breakdown[route]["weight"] += s.weight_kg

    return {
        "total_shipments": total,
        "approved": approved,
        "warnings": warning,
        "rejected": rejected,
        "total_weight_kg": total_weight,
        "total_volume_m3": total_volume,
        "type_breakdown": type_breakdown,
        "route_breakdown": route_breakdown,
    }


# ── Template Context ─────────────────────────────────────────────────────────

@app.context_processor
def inject_globals():
    """Inject global variables into all templates."""
    return {"rules_count": len(EXPERT_RULES)}


# ── Auth Routes ──────────────────────────────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return render_template("register.html")

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Account created successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get("next")
            # Robust open-redirect protection: only allow safe relative paths
            from urllib.parse import urlparse
            if next_page:
                parsed = urlparse(next_page)
                if parsed.scheme or parsed.netloc:
                    next_page = None
            if not next_page or not next_page.startswith("/"):
                next_page = url_for("dashboard")
            flash("Logged in successfully!", "success")
            return redirect(next_page)

        flash("Invalid username or password.", "danger")
        return render_template("login.html")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("login"))


# ── Page Routes ──────────────────────────────────────────────────────────────

@app.route("/")
@login_required
def dashboard():
    """Dashboard with overview of flights, cargo, and conflicts."""
    flight_summary = _get_flight_summary()
    cargo_summary = _get_cargo_summary()

    conflicts = _check_conflicts_from_db()

    return render_template(
        "index.html",
        active_page="dashboard",
        flight_summary=flight_summary,
        cargo_summary=cargo_summary,
        conflicts=conflicts,
    )


@app.route("/flights")
@login_required
def flights_page():
    """Flight scheduling page."""
    records = FlightRecord.query.order_by(FlightRecord.created_at.desc()).all()
    flights = [_flight_record_to_dict(r) for r in records]
    return render_template(
        "flights.html",
        active_page="flights",
        flights=flights,
        aircraft=AIRCRAFT_FLEET,
        airports=AIRPORTS,
    )


@app.route("/cargo")
@login_required
def cargo_page():
    """Cargo scheduling page."""
    records = CargoRecord.query.order_by(CargoRecord.created_at.desc()).all()
    shipments = [_cargo_record_to_dict(r) for r in records]
    cargo_summary = _get_cargo_summary()
    return render_template(
        "cargo.html",
        active_page="cargo",
        shipments=shipments,
        cargo_summary=cargo_summary,
        aircraft=AIRCRAFT_FLEET,
        airports=AIRPORTS,
        cargo_types=CARGO_TYPES,
    )


@app.route("/knowledge")
@login_required
def knowledge_page():
    """Knowledge base viewer page."""
    return render_template(
        "knowledge.html",
        active_page="knowledge",
        aircraft=AIRCRAFT_FLEET,
        airports=AIRPORTS,
        cargo_types=CARGO_TYPES,
        rules=EXPERT_RULES,
        scheduling_rules=SCHEDULING_RULES,
    )


@app.route("/analytics")
@login_required
def analytics_page():
    """Analytics and charts page."""
    flight_summary = _get_flight_summary()
    cargo_summary = _get_cargo_summary()
    return render_template(
        "analytics.html",
        active_page="analytics",
        flight_summary=flight_summary,
        cargo_summary=cargo_summary,
    )


# ── API Routes ───────────────────────────────────────────────────────────────

@app.route("/api/flights", methods=["POST"])
@login_required
def add_flight():
    """Add a new flight and validate it through the inference engine."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    required_fields = ["flight_number", "aircraft", "origin",
                       "destination", "departure_time", "arrival_time"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Validate through inference engine using a request-local scheduler
    # to avoid unbounded in-memory growth on the shared instance
    local_flight_scheduler = FlightScheduler()
    result = local_flight_scheduler.add_flight(
        flight_number=data["flight_number"],
        aircraft=data["aircraft"],
        origin=data["origin"],
        destination=data["destination"],
        departure_time=data["departure_time"],
        arrival_time=data["arrival_time"],
        turnaround_time_min=data.get("turnaround_time_min"),
        crew_duty_hours=data.get("crew_duty_hours"),
        crew_rest_hours=data.get("crew_rest_hours"),
        connection_time_min=data.get("connection_time_min"),
    )

    flight_dict = result["flight"]

    # Persist to database
    rec = FlightRecord(
        flight_number=data["flight_number"],
        aircraft=data["aircraft"],
        origin=data["origin"],
        destination=data["destination"],
        departure_time=data["departure_time"],
        arrival_time=data["arrival_time"],
        turnaround_time_min=data.get("turnaround_time_min"),
        crew_duty_hours=data.get("crew_duty_hours"),
        crew_rest_hours=data.get("crew_rest_hours"),
        connection_time_min=data.get("connection_time_min"),
        status=flight_dict["status"],
        validation_json=json.dumps(flight_dict["validation_results"]),
        user_id=current_user.id,
    )
    db.session.add(rec)
    db.session.commit()

    # Update the id in the response
    flight_dict["id"] = rec.id
    return jsonify(result)


@app.route("/api/flights/<int:flight_id>/delete", methods=["POST"])
@login_required
def delete_flight(flight_id):
    """Delete a flight from the schedule."""
    rec = db.session.get(FlightRecord, flight_id)
    if rec:
        db.session.delete(rec)
        db.session.commit()
    return redirect(url_for("flights_page"))


@app.route("/api/cargo", methods=["POST"])
@login_required
def add_cargo():
    """Add a new cargo shipment and validate it through the inference engine."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    required_fields = ["aircraft", "origin", "destination",
                       "cargo_type", "weight_kg", "volume_m3"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Validate through inference engine using a request-local scheduler
    # to avoid unbounded in-memory growth on the shared instance
    local_cargo_scheduler = CargoScheduler()
    result = local_cargo_scheduler.add_shipment(
        aircraft=data["aircraft"],
        origin=data["origin"],
        destination=data["destination"],
        cargo_type=data["cargo_type"],
        weight_kg=float(data["weight_kg"]),
        volume_m3=float(data["volume_m3"]),
        is_passenger_flight=data.get("is_passenger_flight", True),
        estimated_transit_hours=float(data.get("estimated_transit_hours", 0)),
        description=data.get("description", ""),
    )

    shipment_dict = result["shipment"]

    # Persist to database — generate shipment_number from DB auto-increment ID
    # to avoid duplicates after server restarts
    rec = CargoRecord(
        shipment_number="CRG-TEMP",
        aircraft=data["aircraft"],
        origin=data["origin"],
        destination=data["destination"],
        cargo_type=data["cargo_type"],
        weight_kg=float(data["weight_kg"]),
        volume_m3=float(data["volume_m3"]),
        is_passenger_flight=data.get("is_passenger_flight", True),
        estimated_transit_hours=shipment_dict["estimated_transit_hours"],
        description=data.get("description", ""),
        status=shipment_dict["status"],
        validation_json=json.dumps(shipment_dict["validation_results"]),
        user_id=current_user.id,
    )
    db.session.add(rec)
    db.session.flush()
    rec.shipment_number = f"CRG-{rec.id:04d}"
    db.session.commit()

    shipment_dict["id"] = rec.id
    shipment_dict["shipment_number"] = rec.shipment_number
    return jsonify(result)


@app.route("/api/cargo/<int:shipment_id>/delete", methods=["POST"])
@login_required
def delete_cargo(shipment_id):
    """Delete a cargo shipment."""
    rec = db.session.get(CargoRecord, shipment_id)
    if rec:
        db.session.delete(rec)
        db.session.commit()
    return redirect(url_for("cargo_page"))


@app.route("/api/conflicts", methods=["GET"])
@login_required
def get_conflicts():
    """Get all schedule conflicts."""
    conflicts = _check_conflicts_from_db()
    return jsonify({"conflicts": conflicts})


@app.route("/api/summary", methods=["GET"])
@login_required
def get_summary():
    """Get full system summary."""
    return jsonify({
        "flights": _get_flight_summary(),
        "cargo": _get_cargo_summary(),
    })


@app.route("/api/chart-data", methods=["GET"])
@login_required
def chart_data():
    """Return data for analytics charts."""
    flight_summary = _get_flight_summary()
    cargo_summary = _get_cargo_summary()

    return jsonify({
        "flight_status": {
            "approved": flight_summary["approved"],
            "warnings": flight_summary["warnings"],
            "rejected": flight_summary["rejected"],
        },
        "cargo_status": {
            "approved": cargo_summary["approved"],
            "warnings": cargo_summary["warnings"],
            "rejected": cargo_summary["rejected"],
        },
        "aircraft_usage": flight_summary["aircraft_usage"],
        "route_counts": flight_summary["route_counts"],
        "cargo_type_breakdown": cargo_summary["type_breakdown"],
        "cargo_route_breakdown": cargo_summary["route_breakdown"],
    })


# ── Export Routes ────────────────────────────────────────────────────────────

@app.route("/export/flights/csv")
@login_required
def export_flights_csv():
    """Export all flights as CSV."""
    records = FlightRecord.query.order_by(FlightRecord.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Flight Number", "Aircraft", "Origin", "Destination",
        "Departure", "Arrival", "Status", "Created At",
    ])
    for r in records:
        writer.writerow([
            r.id, r.flight_number, r.aircraft, r.origin, r.destination,
            r.departure_time, r.arrival_time, r.status,
            r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
        ])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=flights_export.csv"},
    )


@app.route("/export/cargo/csv")
@login_required
def export_cargo_csv():
    """Export all cargo shipments as CSV."""
    records = CargoRecord.query.order_by(CargoRecord.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Shipment Number", "Aircraft", "Origin", "Destination",
        "Cargo Type", "Weight (kg)", "Volume (m3)", "Flight Type",
        "Transit Hours", "Status", "Created At",
    ])
    for r in records:
        writer.writerow([
            r.id, r.shipment_number, r.aircraft, r.origin, r.destination,
            r.cargo_type, r.weight_kg, r.volume_m3,
            "Passenger" if r.is_passenger_flight else "Freighter",
            r.estimated_transit_hours, r.status,
            r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
        ])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=cargo_export.csv"},
    )


@app.route("/export/flights/pdf")
@login_required
def export_flights_pdf():
    """Export all flights as PDF."""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    records = FlightRecord.query.order_by(FlightRecord.created_at.desc()).all()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("AeroScheduler - Flight Schedule Report", styles["Title"]))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
        f"Total Flights: {len(records)}",
        styles["Normal"],
    ))
    elements.append(Spacer(1, 12))

    data = [["#", "Flight", "Aircraft", "Origin", "Dest", "Depart", "Arrive", "Status"]]
    for r in records:
        data.append([
            str(r.id), r.flight_number, r.aircraft, r.origin,
            r.destination, r.departure_time, r.arrival_time,
            r.status.upper(),
        ])

    if len(data) > 1:
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a56db")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f2f5")]),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No flights scheduled yet.", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return Response(
        buffer.getvalue(),
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=flights_report.pdf"},
    )


@app.route("/export/cargo/pdf")
@login_required
def export_cargo_pdf():
    """Export all cargo shipments as PDF."""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    records = CargoRecord.query.order_by(CargoRecord.created_at.desc()).all()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("AeroScheduler - Cargo Schedule Report", styles["Title"]))
    elements.append(Spacer(1, 20))
    total_weight = sum(r.weight_kg for r in records)
    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
        f"Total Shipments: {len(records)} | Total Weight: {total_weight} kg",
        styles["Normal"],
    ))
    elements.append(Spacer(1, 12))

    data = [["#", "Shipment", "Aircraft", "Route", "Type", "Weight", "Volume", "Status"]]
    for r in records:
        cargo_info = CARGO_TYPES.get(r.cargo_type, {})
        data.append([
            str(r.id), r.shipment_number, r.aircraft,
            f"{r.origin}-{r.destination}",
            cargo_info.get("name", r.cargo_type),
            f"{r.weight_kg} kg", f"{r.volume_m3} m3",
            r.status.upper(),
        ])

    if len(data) > 1:
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#a855f7")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f2f5")]),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No cargo shipments yet.", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return Response(
        buffer.getvalue(),
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=cargo_report.pdf"},
    )


# ── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
