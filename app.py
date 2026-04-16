"""
AeroScheduler Expert System - Main Flask Application

An expert system for airline flight scheduling and cargo schedule management.
Uses a rule-based inference engine with forward chaining to validate schedules,
detect conflicts, and generate optimization recommendations.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for

from expert_system.knowledge_base import (
    AIRCRAFT_FLEET,
    AIRPORTS,
    CARGO_TYPES,
    EXPERT_RULES,
    SCHEDULING_RULES,
)
from expert_system.flight_scheduler import FlightScheduler
from expert_system.cargo_scheduler import CargoScheduler

app = Flask(__name__)

# Initialize schedulers (in-memory state)
flight_scheduler = FlightScheduler()
cargo_scheduler = CargoScheduler()


# ── Template Context ─────────────────────────────────────────────────────────

@app.context_processor
def inject_globals():
    """Inject global variables into all templates."""
    return {"rules_count": len(EXPERT_RULES)}


# ── Page Routes ──────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    """Dashboard with overview of flights, cargo, and conflicts."""
    flight_summary = flight_scheduler.get_schedule_summary()
    cargo_summary = cargo_scheduler.get_cargo_summary()
    conflicts = flight_scheduler.check_conflicts()
    return render_template(
        "index.html",
        active_page="dashboard",
        flight_summary=flight_summary,
        cargo_summary=cargo_summary,
        conflicts=conflicts,
    )


@app.route("/flights")
def flights_page():
    """Flight scheduling page."""
    flights = flight_scheduler.get_all_flights()
    return render_template(
        "flights.html",
        active_page="flights",
        flights=flights,
        aircraft=AIRCRAFT_FLEET,
        airports=AIRPORTS,
    )


@app.route("/cargo")
def cargo_page():
    """Cargo scheduling page."""
    shipments = cargo_scheduler.get_all_shipments()
    cargo_summary = cargo_scheduler.get_cargo_summary()
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


# ── API Routes ───────────────────────────────────────────────────────────────

@app.route("/api/flights", methods=["POST"])
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

    result = flight_scheduler.add_flight(
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
    return jsonify(result)


@app.route("/api/flights/<int:flight_id>/delete", methods=["POST"])
def delete_flight(flight_id):
    """Delete a flight from the schedule."""
    flight_scheduler.delete_flight(flight_id)
    return redirect(url_for("flights_page"))


@app.route("/api/cargo", methods=["POST"])
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

    result = cargo_scheduler.add_shipment(
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
    return jsonify(result)


@app.route("/api/cargo/<int:shipment_id>/delete", methods=["POST"])
def delete_cargo(shipment_id):
    """Delete a cargo shipment."""
    cargo_scheduler.delete_shipment(shipment_id)
    return redirect(url_for("cargo_page"))


@app.route("/api/cargo/optimize/<aircraft_id>", methods=["GET"])
def optimize_cargo(aircraft_id):
    """Get optimized cargo loading plan for a given aircraft."""
    result = cargo_scheduler.optimize_loading(aircraft_id)
    return jsonify(result)


@app.route("/api/conflicts", methods=["GET"])
def get_conflicts():
    """Get all schedule conflicts."""
    conflicts = flight_scheduler.check_conflicts()
    return jsonify({"conflicts": conflicts})


@app.route("/api/summary", methods=["GET"])
def get_summary():
    """Get full system summary."""
    return jsonify({
        "flights": flight_scheduler.get_schedule_summary(),
        "cargo": cargo_scheduler.get_cargo_summary(),
        "conflicts": flight_scheduler.check_conflicts(),
    })


# ── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
