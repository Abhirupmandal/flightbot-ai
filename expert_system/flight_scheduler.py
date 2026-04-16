"""
Flight Scheduler Module.

Manages flight schedules, validates them against the expert rules,
and provides schedule optimization suggestions.
"""

from datetime import datetime, timedelta

from expert_system.knowledge_base import (
    AIRCRAFT_FLEET,
    AIRPORTS,
    SCHEDULING_RULES,
    get_route_distance,
)
from expert_system.inference_engine import InferenceEngine


class Flight:
    """Represents a single scheduled flight."""

    _next_id = 1

    def __init__(self, flight_number, aircraft, origin, destination,
                 departure_time, arrival_time, turnaround_time_min=None,
                 crew_duty_hours=None, crew_rest_hours=None,
                 connection_time_min=None):
        self.id = Flight._next_id
        Flight._next_id += 1
        self.flight_number = flight_number
        self.aircraft = aircraft
        self.origin = origin
        self.destination = destination
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.turnaround_time_min = turnaround_time_min
        self.crew_duty_hours = crew_duty_hours
        self.crew_rest_hours = crew_rest_hours
        self.connection_time_min = connection_time_min
        self.status = "scheduled"
        self.validation_results = []

    def to_dict(self):
        distance = get_route_distance(self.origin, self.destination)
        aircraft_info = AIRCRAFT_FLEET.get(self.aircraft, {})
        return {
            "id": self.id,
            "flight_number": self.flight_number,
            "aircraft": self.aircraft,
            "aircraft_type": aircraft_info.get("type", "Unknown"),
            "origin": self.origin,
            "origin_name": AIRPORTS.get(self.origin, {}).get("name", "Unknown"),
            "destination": self.destination,
            "destination_name": AIRPORTS.get(self.destination, {}).get("name", "Unknown"),
            "departure_time": self.departure_time,
            "arrival_time": self.arrival_time,
            "distance_km": distance,
            "turnaround_time_min": self.turnaround_time_min,
            "crew_duty_hours": self.crew_duty_hours,
            "crew_rest_hours": self.crew_rest_hours,
            "connection_time_min": self.connection_time_min,
            "status": self.status,
            "validation_results": [r.to_dict() for r in self.validation_results],
        }


class FlightScheduler:
    """Manages flight schedules and validates them using the inference engine."""

    def __init__(self):
        self.flights = []
        self.engine = InferenceEngine()

    def add_flight(self, flight_number, aircraft, origin, destination,
                   departure_time, arrival_time, turnaround_time_min=None,
                   crew_duty_hours=None, crew_rest_hours=None,
                   connection_time_min=None):
        """Add a new flight and validate it against expert rules."""
        flight = Flight(
            flight_number=flight_number,
            aircraft=aircraft,
            origin=origin,
            destination=destination,
            departure_time=departure_time,
            arrival_time=arrival_time,
            turnaround_time_min=turnaround_time_min,
            crew_duty_hours=crew_duty_hours,
            crew_rest_hours=crew_rest_hours,
            connection_time_min=connection_time_min,
        )

        # Validate through inference engine
        flight_data = {
            "aircraft": aircraft,
            "origin": origin,
            "destination": destination,
            "departure_time": departure_time,
            "arrival_time": arrival_time,
            "turnaround_time_min": turnaround_time_min,
            "crew_duty_hours": crew_duty_hours,
            "crew_rest_hours": crew_rest_hours,
            "connection_time_min": connection_time_min,
        }

        results = self.engine.evaluate_flight(flight_data)
        flight.validation_results = results

        # Set status based on results
        has_critical = any(r.severity == "critical" for r in results)
        has_high = any(r.severity == "high" for r in results)

        if has_critical:
            flight.status = "rejected"
        elif has_high:
            flight.status = "warning"
        else:
            flight.status = "approved"

        self.flights.append(flight)

        # Get recommendations
        recommendations = self.engine.get_recommendations(
            flight_data=flight_data
        )

        return {
            "flight": flight.to_dict(),
            "recommendations": recommendations,
        }

    def get_all_flights(self):
        """Return all scheduled flights."""
        return [f.to_dict() for f in self.flights]

    def delete_flight(self, flight_id):
        """Remove a flight by ID."""
        self.flights = [f for f in self.flights if f.id != flight_id]

    def check_conflicts(self):
        """Check for scheduling conflicts between all flights."""
        conflicts = []
        for i, f1 in enumerate(self.flights):
            for f2 in self.flights[i + 1:]:
                # Same aircraft, overlapping times
                if f1.aircraft == f2.aircraft:
                    if self._times_overlap(
                        f1.departure_time, f1.arrival_time,
                        f2.departure_time, f2.arrival_time,
                    ):
                        conflicts.append({
                            "type": "aircraft_conflict",
                            "severity": "critical",
                            "message": (
                                f"Aircraft {f1.aircraft} is double-booked: "
                                f"{f1.flight_number} ({f1.departure_time}-"
                                f"{f1.arrival_time}) and "
                                f"{f2.flight_number} ({f2.departure_time}-"
                                f"{f2.arrival_time})"
                            ),
                            "flights": [f1.flight_number, f2.flight_number],
                        })

                # Same origin/destination at similar times (gate conflict)
                if f1.origin == f2.origin:
                    if self._times_close(f1.departure_time,
                                         f2.departure_time, 15):
                        conflicts.append({
                            "type": "gate_conflict",
                            "severity": "medium",
                            "message": (
                                f"Flights {f1.flight_number} and "
                                f"{f2.flight_number} depart from {f1.origin} "
                                f"within 15 min of each other. Potential "
                                f"gate conflict."
                            ),
                            "flights": [f1.flight_number, f2.flight_number],
                        })

        return conflicts

    def get_schedule_summary(self):
        """Return a summary of the current schedule."""
        total = len(self.flights)
        approved = sum(1 for f in self.flights if f.status == "approved")
        warning = sum(1 for f in self.flights if f.status == "warning")
        rejected = sum(1 for f in self.flights if f.status == "rejected")

        aircraft_usage = {}
        for f in self.flights:
            aircraft_usage.setdefault(f.aircraft, 0)
            aircraft_usage[f.aircraft] += 1

        route_counts = {}
        for f in self.flights:
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

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _to_minutes(time_str):
        """Convert HH:MM string to minutes since midnight."""
        h, m = map(int, time_str.split(":"))
        return h * 60 + m

    @staticmethod
    def _times_overlap(dep1, arr1, dep2, arr2):
        """Check if two time ranges overlap (HH:MM strings).

        Handles overnight flights where arrival < departure by treating
        the arrival as being on the next day.
        """
        try:
            d1 = FlightScheduler._to_minutes(dep1)
            a1 = FlightScheduler._to_minutes(arr1)
            d2 = FlightScheduler._to_minutes(dep2)
            a2 = FlightScheduler._to_minutes(arr2)
            # If arrival is before departure, the flight crosses midnight
            if a1 <= d1:
                a1 += 24 * 60
            if a2 <= d2:
                a2 += 24 * 60
            return d1 < a2 and d2 < a1
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def _times_close(t1, t2, threshold_min):
        """Check if two HH:MM times are within threshold_min of each other."""
        try:
            m1 = FlightScheduler._to_minutes(t1)
            m2 = FlightScheduler._to_minutes(t2)
            diff = abs(m1 - m2)
            # Account for wrap-around midnight
            diff = min(diff, 24 * 60 - diff)
            return diff <= threshold_min
        except (ValueError, AttributeError):
            return False
