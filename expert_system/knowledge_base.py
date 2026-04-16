"""
Knowledge Base for the Airline Scheduling and Cargo Schedules Expert System.

Contains:
- Facts: Aircraft data, airport data, cargo types, crew rules
- Rules: Scheduling constraints, cargo restrictions, optimization heuristics
"""

from datetime import datetime, timedelta


# ── Aircraft Fleet Database ──────────────────────────────────────────────────

AIRCRAFT_FLEET = {
    "B737-800": {
        "type": "Boeing 737-800",
        "max_range_km": 5765,
        "max_passengers": 189,
        "cargo_capacity_kg": 5500,
        "cargo_volume_m3": 45,
        "fuel_burn_per_hour_kg": 2500,
        "turnaround_time_min": 45,
        "max_flight_hours_per_day": 14,
        "category": "narrow-body",
    },
    "A320neo": {
        "type": "Airbus A320neo",
        "max_range_km": 6300,
        "max_passengers": 194,
        "cargo_capacity_kg": 6000,
        "cargo_volume_m3": 50,
        "fuel_burn_per_hour_kg": 2200,
        "turnaround_time_min": 45,
        "max_flight_hours_per_day": 14,
        "category": "narrow-body",
    },
    "B777-300ER": {
        "type": "Boeing 777-300ER",
        "max_range_km": 13650,
        "max_passengers": 396,
        "cargo_capacity_kg": 23000,
        "cargo_volume_m3": 200,
        "fuel_burn_per_hour_kg": 6800,
        "turnaround_time_min": 90,
        "max_flight_hours_per_day": 18,
        "category": "wide-body",
    },
    "A350-900": {
        "type": "Airbus A350-900",
        "max_range_km": 15000,
        "max_passengers": 325,
        "cargo_capacity_kg": 20000,
        "cargo_volume_m3": 180,
        "fuel_burn_per_hour_kg": 5800,
        "turnaround_time_min": 90,
        "max_flight_hours_per_day": 18,
        "category": "wide-body",
    },
    "B747-400F": {
        "type": "Boeing 747-400F (Freighter)",
        "max_range_km": 8230,
        "max_passengers": 0,
        "cargo_capacity_kg": 112760,
        "cargo_volume_m3": 858,
        "fuel_burn_per_hour_kg": 10500,
        "turnaround_time_min": 120,
        "max_flight_hours_per_day": 16,
        "category": "freighter",
    },
    "A330-200F": {
        "type": "Airbus A330-200F (Freighter)",
        "max_range_km": 7400,
        "max_passengers": 0,
        "cargo_capacity_kg": 70000,
        "cargo_volume_m3": 475,
        "fuel_burn_per_hour_kg": 5900,
        "turnaround_time_min": 100,
        "max_flight_hours_per_day": 16,
        "category": "freighter",
    },
}


# ── Airport Database ─────────────────────────────────────────────────────────

AIRPORTS = {
    "JFK": {
        "name": "John F. Kennedy International",
        "city": "New York",
        "country": "USA",
        "timezone": "UTC-5",
        "hub": True,
        "cargo_facility": True,
        "curfew_start": None,
        "curfew_end": None,
        "peak_hours": [(7, 10), (16, 20)],
    },
    "LAX": {
        "name": "Los Angeles International",
        "city": "Los Angeles",
        "country": "USA",
        "timezone": "UTC-8",
        "hub": True,
        "cargo_facility": True,
        "curfew_start": None,
        "curfew_end": None,
        "peak_hours": [(7, 10), (16, 20)],
    },
    "LHR": {
        "name": "London Heathrow",
        "city": "London",
        "country": "UK",
        "timezone": "UTC+0",
        "hub": True,
        "cargo_facility": True,
        "curfew_start": 23,
        "curfew_end": 6,
        "peak_hours": [(6, 9), (17, 21)],
    },
    "DXB": {
        "name": "Dubai International",
        "city": "Dubai",
        "country": "UAE",
        "timezone": "UTC+4",
        "hub": True,
        "cargo_facility": True,
        "curfew_start": None,
        "curfew_end": None,
        "peak_hours": [(8, 11), (18, 22)],
    },
    "SIN": {
        "name": "Singapore Changi",
        "city": "Singapore",
        "country": "Singapore",
        "timezone": "UTC+8",
        "hub": True,
        "cargo_facility": True,
        "curfew_start": None,
        "curfew_end": None,
        "peak_hours": [(7, 10), (17, 21)],
    },
    "HKG": {
        "name": "Hong Kong International",
        "city": "Hong Kong",
        "country": "China",
        "timezone": "UTC+8",
        "hub": True,
        "cargo_facility": True,
        "curfew_start": None,
        "curfew_end": None,
        "peak_hours": [(8, 11), (18, 22)],
    },
    "FRA": {
        "name": "Frankfurt Airport",
        "city": "Frankfurt",
        "country": "Germany",
        "timezone": "UTC+1",
        "hub": True,
        "cargo_facility": True,
        "curfew_start": 23,
        "curfew_end": 5,
        "peak_hours": [(6, 9), (16, 20)],
    },
    "ORD": {
        "name": "O'Hare International",
        "city": "Chicago",
        "country": "USA",
        "timezone": "UTC-6",
        "hub": True,
        "cargo_facility": True,
        "curfew_start": None,
        "curfew_end": None,
        "peak_hours": [(7, 10), (16, 20)],
    },
}


# ── Route Distances (km) ────────────────────────────────────────────────────

ROUTE_DISTANCES = {
    ("JFK", "LAX"): 3983,
    ("JFK", "LHR"): 5539,
    ("JFK", "DXB"): 11023,
    ("JFK", "ORD"): 1188,
    ("JFK", "FRA"): 6198,
    ("LAX", "SIN"): 14114,
    ("LAX", "HKG"): 11654,
    ("LAX", "ORD"): 2807,
    ("LHR", "DXB"): 5475,
    ("LHR", "SIN"): 10852,
    ("LHR", "HKG"): 9613,
    ("LHR", "FRA"): 660,
    ("DXB", "SIN"): 5845,
    ("DXB", "HKG"): 5962,
    ("SIN", "HKG"): 2581,
    ("FRA", "DXB"): 4833,
    ("FRA", "SIN"): 10290,
    ("ORD", "LHR"): 6364,
    ("ORD", "FRA"): 6973,
}


def get_route_distance(origin, destination):
    """Return distance in km between two airports (bidirectional lookup)."""
    key = (origin, destination)
    reverse_key = (destination, origin)
    if key in ROUTE_DISTANCES:
        return ROUTE_DISTANCES[key]
    if reverse_key in ROUTE_DISTANCES:
        return ROUTE_DISTANCES[reverse_key]
    return None


# ── Cargo Types & Restrictions ───────────────────────────────────────────────

CARGO_TYPES = {
    "general": {
        "name": "General Cargo",
        "priority": 3,
        "requires_temp_control": False,
        "hazardous": False,
        "max_transit_hours": 72,
        "handling_time_min": 30,
        "description": "Standard goods, non-perishable, non-hazardous",
    },
    "perishable": {
        "name": "Perishable Goods",
        "priority": 1,
        "requires_temp_control": True,
        "hazardous": False,
        "max_transit_hours": 24,
        "handling_time_min": 45,
        "description": "Food, flowers, pharmaceuticals requiring temperature control",
    },
    "hazardous": {
        "name": "Hazardous Materials",
        "priority": 2,
        "requires_temp_control": False,
        "hazardous": True,
        "max_transit_hours": 48,
        "handling_time_min": 60,
        "description": "Chemicals, batteries, flammable goods (IATA DGR compliant)",
    },
    "live_animals": {
        "name": "Live Animals",
        "priority": 1,
        "requires_temp_control": True,
        "hazardous": False,
        "max_transit_hours": 18,
        "handling_time_min": 60,
        "description": "Live animals requiring special handling and ventilation",
    },
    "valuable": {
        "name": "Valuable Cargo",
        "priority": 2,
        "requires_temp_control": False,
        "hazardous": False,
        "max_transit_hours": 48,
        "handling_time_min": 45,
        "description": "High-value items: electronics, jewelry, documents",
    },
    "oversized": {
        "name": "Oversized / Heavy Cargo",
        "priority": 4,
        "requires_temp_control": False,
        "hazardous": False,
        "max_transit_hours": 96,
        "handling_time_min": 90,
        "description": "Machinery, vehicles, or unusually large items",
    },
}


# ── Scheduling Rules ─────────────────────────────────────────────────────────

SCHEDULING_RULES = {
    "min_connection_time_min": 60,
    "max_crew_flight_hours_per_day": 10,
    "max_crew_duty_hours_per_day": 14,
    "min_crew_rest_hours": 10,
    "max_consecutive_duty_days": 6,
    "min_turnaround_narrow_body_min": 45,
    "min_turnaround_wide_body_min": 90,
    "min_turnaround_freighter_min": 120,
    "buffer_time_peak_hours_min": 15,
    "max_delay_before_cancel_min": 180,
    "weather_buffer_min": 30,
    "hazmat_separation_min": 30,
    "max_hazmat_per_flight_kg": 500,
    "live_animal_max_transit_hours": 18,
}


# ── Expert Rules (IF-THEN format) ───────────────────────────────────────────

EXPERT_RULES = [
    {
        "id": "R01",
        "name": "Aircraft Range Check",
        "category": "flight",
        "condition": "route_distance > aircraft_max_range",
        "action": "reject_schedule",
        "message": "Aircraft {aircraft} cannot cover route {origin}-{destination} "
                   "({distance} km exceeds max range {max_range} km). "
                   "Recommend using a long-range aircraft.",
        "severity": "critical",
    },
    {
        "id": "R02",
        "name": "Turnaround Time Check",
        "category": "flight",
        "condition": "turnaround_time < min_turnaround",
        "action": "warn_schedule",
        "message": "Insufficient turnaround time at {airport}. "
                   "Minimum {min_turnaround} min required for {aircraft_category}, "
                   "but only {available_time} min scheduled.",
        "severity": "high",
    },
    {
        "id": "R03",
        "name": "Night Curfew Check",
        "category": "flight",
        "condition": "arrival_or_departure_during_curfew",
        "action": "reject_schedule",
        "message": "Airport {airport} has a noise curfew from {curfew_start}:00 "
                   "to {curfew_end}:00. Flight scheduled at {time} violates curfew.",
        "severity": "critical",
    },
    {
        "id": "R04",
        "name": "Crew Duty Hours",
        "category": "crew",
        "condition": "crew_duty_hours > max_duty_hours",
        "action": "reject_schedule",
        "message": "Crew duty time ({duty_hours}h) exceeds maximum allowed "
                   "({max_hours}h). Schedule a crew change or rest period.",
        "severity": "critical",
    },
    {
        "id": "R05",
        "name": "Crew Rest Requirement",
        "category": "crew",
        "condition": "crew_rest < min_rest_hours",
        "action": "reject_schedule",
        "message": "Crew rest period ({rest_hours}h) is below minimum "
                   "({min_rest}h). Adjust schedule to allow adequate rest.",
        "severity": "critical",
    },
    {
        "id": "R06",
        "name": "Cargo Weight Limit",
        "category": "cargo",
        "condition": "total_cargo_weight > aircraft_cargo_capacity",
        "action": "reject_cargo",
        "message": "Total cargo weight ({total_weight} kg) exceeds aircraft "
                   "{aircraft} capacity ({capacity} kg). Reduce load or use "
                   "a larger aircraft.",
        "severity": "critical",
    },
    {
        "id": "R07",
        "name": "Cargo Volume Limit",
        "category": "cargo",
        "condition": "total_cargo_volume > aircraft_cargo_volume",
        "action": "reject_cargo",
        "message": "Total cargo volume ({total_volume} m³) exceeds aircraft "
                   "{aircraft} hold volume ({capacity} m³). Reduce load or "
                   "split across flights.",
        "severity": "critical",
    },
    {
        "id": "R08",
        "name": "Hazardous Cargo Limit",
        "category": "cargo",
        "condition": "hazmat_weight > max_hazmat_per_flight",
        "action": "reject_cargo",
        "message": "Hazardous material weight ({hazmat_weight} kg) exceeds "
                   "limit ({max_hazmat} kg per flight). Split hazmat across "
                   "multiple flights.",
        "severity": "critical",
    },
    {
        "id": "R09",
        "name": "Perishable Transit Time",
        "category": "cargo",
        "condition": "transit_time > perishable_max_transit",
        "action": "warn_cargo",
        "message": "Estimated transit time ({transit_time}h) exceeds maximum "
                   "for perishable cargo ({max_transit}h). Consider a direct "
                   "route or faster connection.",
        "severity": "high",
    },
    {
        "id": "R10",
        "name": "Live Animal Transit",
        "category": "cargo",
        "condition": "transit_time > live_animal_max_transit",
        "action": "reject_cargo",
        "message": "Estimated transit time ({transit_time}h) exceeds maximum "
                   "for live animal transport ({max_transit}h). Use a direct "
                   "flight or shorter route.",
        "severity": "critical",
    },
    {
        "id": "R11",
        "name": "Peak Hour Buffer",
        "category": "flight",
        "condition": "departure_during_peak_and_no_buffer",
        "action": "warn_schedule",
        "message": "Flight departs during peak hours at {airport}. Adding "
                   "{buffer} min buffer to scheduled time is recommended.",
        "severity": "medium",
    },
    {
        "id": "R12",
        "name": "Cargo Facility Check",
        "category": "cargo",
        "condition": "airport_has_no_cargo_facility",
        "action": "reject_cargo",
        "message": "Airport {airport} does not have cargo handling facilities. "
                   "Choose an alternate airport with cargo support.",
        "severity": "critical",
    },
    {
        "id": "R13",
        "name": "Hazmat-Passenger Separation",
        "category": "cargo",
        "condition": "hazmat_on_passenger_flight",
        "action": "warn_cargo",
        "message": "Hazardous cargo on passenger flight {flight}. Ensure IATA "
                   "DGR compliance and weight is within passenger-flight limits. "
                   "Max {max_hazmat} kg allowed.",
        "severity": "high",
    },
    {
        "id": "R14",
        "name": "Freighter Recommendation",
        "category": "cargo",
        "condition": "cargo_weight_high_and_no_passengers",
        "action": "recommend",
        "message": "Cargo-only shipment of {weight} kg detected. Recommend "
                   "using a dedicated freighter aircraft for optimal capacity.",
        "severity": "info",
    },
    {
        "id": "R15",
        "name": "Connection Time Check",
        "category": "flight",
        "condition": "connection_time < min_connection_time",
        "action": "reject_schedule",
        "message": "Connection time at {airport} is {conn_time} min, below "
                   "the minimum of {min_conn} min. Passengers and cargo may "
                   "miss connecting flight.",
        "severity": "critical",
    },
]
