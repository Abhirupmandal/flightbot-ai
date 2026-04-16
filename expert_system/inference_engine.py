"""
Inference Engine for the Airline Scheduling and Cargo Schedules Expert System.

Implements forward-chaining rule evaluation to validate schedules,
detect conflicts, and generate recommendations.
"""

from datetime import datetime, timedelta

from expert_system.knowledge_base import (
    AIRCRAFT_FLEET,
    AIRPORTS,
    CARGO_TYPES,
    EXPERT_RULES,
    SCHEDULING_RULES,
    get_route_distance,
)


class InferenceResult:
    """Represents the result of a single rule evaluation."""

    def __init__(self, rule_id, rule_name, severity, message, action, category):
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.severity = severity
        self.message = message
        self.action = action
        self.category = category

    def to_dict(self):
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity,
            "message": self.message,
            "action": self.action,
            "category": self.category,
        }


class InferenceEngine:
    """
    Forward-chaining inference engine.

    Evaluates all applicable rules against the provided facts
    and returns a list of findings (warnings, rejections, recommendations).
    """

    def __init__(self):
        self.rules = EXPERT_RULES
        self.results = []

    def clear(self):
        self.results = []

    # ── Public API ───────────────────────────────────────────────────────

    def evaluate_flight(self, flight_data):
        """
        Evaluate scheduling rules for a single flight.

        flight_data dict keys:
            aircraft, origin, destination,
            departure_time (HH:MM), arrival_time (HH:MM),
            turnaround_time_min (optional), crew_duty_hours (optional),
            crew_rest_hours (optional), connection_time_min (optional)
        """
        self.clear()
        aircraft_id = flight_data.get("aircraft", "")
        origin = flight_data.get("origin", "")
        destination = flight_data.get("destination", "")

        aircraft = AIRCRAFT_FLEET.get(aircraft_id)
        origin_airport = AIRPORTS.get(origin)
        dest_airport = AIRPORTS.get(destination)

        if not aircraft:
            self.results.append(InferenceResult(
                "SYS", "Unknown Aircraft", "critical",
                f"Aircraft '{aircraft_id}' not found in fleet database.",
                "reject_schedule", "flight",
            ))
            return self.results

        if not origin_airport:
            self.results.append(InferenceResult(
                "SYS", "Unknown Origin", "critical",
                f"Origin airport '{origin}' not found in database.",
                "reject_schedule", "flight",
            ))
            return self.results

        if not dest_airport:
            self.results.append(InferenceResult(
                "SYS", "Unknown Destination", "critical",
                f"Destination airport '{destination}' not found in database.",
                "reject_schedule", "flight",
            ))
            return self.results

        # R01 – Aircraft Range Check
        distance = get_route_distance(origin, destination)
        if distance and distance > aircraft["max_range_km"]:
            self._fire_rule("R01", aircraft=aircraft_id,
                            origin=origin, destination=destination,
                            distance=distance,
                            max_range=aircraft["max_range_km"])

        # R02 – Turnaround Time Check
        turnaround = flight_data.get("turnaround_time_min")
        if turnaround is not None:
            cat = aircraft["category"]
            if cat == "freighter":
                min_ta = SCHEDULING_RULES["min_turnaround_freighter_min"]
            elif cat == "wide-body":
                min_ta = SCHEDULING_RULES["min_turnaround_wide_body_min"]
            else:
                min_ta = SCHEDULING_RULES["min_turnaround_narrow_body_min"]
            if turnaround < min_ta:
                self._fire_rule("R02", airport=origin,
                                min_turnaround=min_ta,
                                aircraft_category=cat,
                                available_time=turnaround)

        # R03 – Night Curfew (departure)
        dep_time_str = flight_data.get("departure_time", "")
        if dep_time_str and origin_airport.get("curfew_start") is not None:
            dep_hour = int(dep_time_str.split(":")[0])
            if self._is_during_curfew(dep_hour,
                                      origin_airport["curfew_start"],
                                      origin_airport["curfew_end"]):
                self._fire_rule("R03", airport=origin,
                                curfew_start=origin_airport["curfew_start"],
                                curfew_end=origin_airport["curfew_end"],
                                time=dep_time_str)

        # R03 – Night Curfew (arrival)
        arr_time_str = flight_data.get("arrival_time", "")
        if arr_time_str and dest_airport.get("curfew_start") is not None:
            arr_hour = int(arr_time_str.split(":")[0])
            if self._is_during_curfew(arr_hour,
                                      dest_airport["curfew_start"],
                                      dest_airport["curfew_end"]):
                self._fire_rule("R03", airport=destination,
                                curfew_start=dest_airport["curfew_start"],
                                curfew_end=dest_airport["curfew_end"],
                                time=arr_time_str)

        # R04 – Crew Duty Hours
        crew_duty = flight_data.get("crew_duty_hours")
        if crew_duty is not None:
            max_duty = SCHEDULING_RULES["max_crew_duty_hours_per_day"]
            if crew_duty > max_duty:
                self._fire_rule("R04", duty_hours=crew_duty,
                                max_hours=max_duty)

        # R05 – Crew Rest
        crew_rest = flight_data.get("crew_rest_hours")
        if crew_rest is not None:
            min_rest = SCHEDULING_RULES["min_crew_rest_hours"]
            if crew_rest < min_rest:
                self._fire_rule("R05", rest_hours=crew_rest,
                                min_rest=min_rest)

        # R11 – Peak Hour Buffer
        if dep_time_str and origin_airport.get("peak_hours"):
            dep_hour = int(dep_time_str.split(":")[0])
            for start, end in origin_airport["peak_hours"]:
                if start <= dep_hour < end:
                    self._fire_rule("R11", airport=origin,
                                    buffer=SCHEDULING_RULES[
                                        "buffer_time_peak_hours_min"])
                    break

        # R15 – Connection Time
        conn_time = flight_data.get("connection_time_min")
        if conn_time is not None:
            min_conn = SCHEDULING_RULES["min_connection_time_min"]
            if conn_time < min_conn:
                self._fire_rule("R15", airport=destination,
                                conn_time=conn_time, min_conn=min_conn)

        # If no issues found, add a success result
        if not self.results:
            self.results.append(InferenceResult(
                "OK", "Schedule Valid", "info",
                f"Flight {origin} → {destination} on {aircraft_id} "
                f"passes all scheduling rules.",
                "approve", "flight",
            ))

        return self.results

    def evaluate_cargo(self, cargo_data):
        """
        Evaluate cargo rules for a shipment.

        cargo_data dict keys:
            aircraft, origin, destination,
            cargo_type, weight_kg, volume_m3,
            is_passenger_flight (bool), estimated_transit_hours
        """
        self.clear()
        aircraft_id = cargo_data.get("aircraft", "")
        origin = cargo_data.get("origin", "")
        destination = cargo_data.get("destination", "")
        cargo_type = cargo_data.get("cargo_type", "general")
        weight = cargo_data.get("weight_kg", 0)
        volume = cargo_data.get("volume_m3", 0)
        is_pax = cargo_data.get("is_passenger_flight", True)
        transit_hours = cargo_data.get("estimated_transit_hours", 0)

        aircraft = AIRCRAFT_FLEET.get(aircraft_id)
        origin_airport = AIRPORTS.get(origin)
        dest_airport = AIRPORTS.get(destination)
        cargo_info = CARGO_TYPES.get(cargo_type)

        if not aircraft:
            self.results.append(InferenceResult(
                "SYS", "Unknown Aircraft", "critical",
                f"Aircraft '{aircraft_id}' not found in fleet database.",
                "reject_cargo", "cargo",
            ))
            return self.results

        if not cargo_info:
            self.results.append(InferenceResult(
                "SYS", "Unknown Cargo Type", "critical",
                f"Cargo type '{cargo_type}' not recognized.",
                "reject_cargo", "cargo",
            ))
            return self.results

        # R06 – Cargo Weight Limit
        if weight > aircraft["cargo_capacity_kg"]:
            self._fire_rule("R06", total_weight=weight,
                            aircraft=aircraft_id,
                            capacity=aircraft["cargo_capacity_kg"])

        # R07 – Cargo Volume Limit
        if volume > aircraft["cargo_volume_m3"]:
            self._fire_rule("R07", total_volume=volume,
                            aircraft=aircraft_id,
                            capacity=aircraft["cargo_volume_m3"])

        # R08 – Hazmat Weight Limit
        if cargo_info["hazardous"]:
            max_hazmat = SCHEDULING_RULES["max_hazmat_per_flight_kg"]
            if weight > max_hazmat:
                self._fire_rule("R08", hazmat_weight=weight,
                                max_hazmat=max_hazmat)

        # R09 – Perishable Transit Time
        if cargo_type == "perishable":
            max_transit = cargo_info["max_transit_hours"]
            if transit_hours > max_transit:
                self._fire_rule("R09", transit_time=transit_hours,
                                max_transit=max_transit)

        # R10 – Live Animal Transit
        if cargo_type == "live_animals":
            max_transit = SCHEDULING_RULES["live_animal_max_transit_hours"]
            if transit_hours > max_transit:
                self._fire_rule("R10", transit_time=transit_hours,
                                max_transit=max_transit)

        # R12 – Cargo Facility Check
        if origin_airport and not origin_airport.get("cargo_facility", False):
            self._fire_rule("R12", airport=origin)
        if dest_airport and not dest_airport.get("cargo_facility", False):
            self._fire_rule("R12", airport=destination)

        # R13 – Hazmat on Passenger Flight
        if cargo_info["hazardous"] and is_pax:
            max_hazmat = SCHEDULING_RULES["max_hazmat_per_flight_kg"]
            self._fire_rule("R13", flight=f"{origin}-{destination}",
                            max_hazmat=max_hazmat)

        # R14 – Freighter Recommendation
        if weight > 10000 and not is_pax:
            self._fire_rule("R14", weight=weight)

        # If no issues found
        if not self.results:
            self.results.append(InferenceResult(
                "OK", "Cargo Valid", "info",
                f"Cargo shipment ({cargo_info['name']}, {weight} kg) "
                f"on {aircraft_id} passes all cargo rules.",
                "approve", "cargo",
            ))

        return self.results

    def get_recommendations(self, flight_data=None, cargo_data=None):
        """Generate smart recommendations based on input data."""
        recommendations = []

        if flight_data:
            aircraft_id = flight_data.get("aircraft", "")
            origin = flight_data.get("origin", "")
            destination = flight_data.get("destination", "")
            distance = get_route_distance(origin, destination)

            if distance:
                # Recommend best aircraft for route
                suitable = []
                for aid, ainfo in AIRCRAFT_FLEET.items():
                    if ainfo["max_range_km"] >= distance:
                        efficiency = distance / ainfo["fuel_burn_per_hour_kg"]
                        suitable.append((aid, ainfo, efficiency))
                suitable.sort(key=lambda x: x[2], reverse=True)

                if suitable:
                    best = suitable[0]
                    recommendations.append({
                        "type": "aircraft_recommendation",
                        "title": "Optimal Aircraft",
                        "message": f"For {origin} → {destination} "
                                   f"({distance} km), the most fuel-efficient "
                                   f"aircraft is {best[0]} ({best[1]['type']}).",
                        "severity": "info",
                    })

                # Estimate flight duration (avg speed 850 km/h)
                est_hours = round(distance / 850, 1)
                recommendations.append({
                    "type": "time_estimate",
                    "title": "Estimated Flight Duration",
                    "message": f"Estimated flight time for {origin} → "
                               f"{destination}: ~{est_hours} hours.",
                    "severity": "info",
                })

        if cargo_data:
            cargo_type = cargo_data.get("cargo_type", "general")
            weight = cargo_data.get("weight_kg", 0)
            cargo_info = CARGO_TYPES.get(cargo_type)

            if cargo_info:
                # Recommend suitable aircraft for cargo
                suitable = []
                for aid, ainfo in AIRCRAFT_FLEET.items():
                    if ainfo["cargo_capacity_kg"] >= weight:
                        utilization = (weight / ainfo["cargo_capacity_kg"]) * 100
                        suitable.append((aid, ainfo, utilization))
                suitable.sort(key=lambda x: x[2], reverse=True)

                if suitable:
                    best = suitable[0]
                    recommendations.append({
                        "type": "cargo_aircraft",
                        "title": "Best Aircraft for Cargo",
                        "message": f"For {weight} kg of {cargo_info['name']}, "
                                   f"recommend {best[0]} ({best[1]['type']}) "
                                   f"with {best[2]:.0f}% cargo utilization.",
                        "severity": "info",
                    })

                if cargo_info["requires_temp_control"]:
                    recommendations.append({
                        "type": "handling_note",
                        "title": "Temperature Control Required",
                        "message": f"{cargo_info['name']} requires temperature-"
                                   f"controlled handling. Ensure cold chain "
                                   f"facilities are available at both airports.",
                        "severity": "medium",
                    })

                if cargo_info["hazardous"]:
                    recommendations.append({
                        "type": "handling_note",
                        "title": "Hazardous Material Handling",
                        "message": "IATA Dangerous Goods Regulations (DGR) "
                                   "apply. Ensure proper packaging, labeling, "
                                   "and documentation before loading.",
                        "severity": "high",
                    })

        return recommendations

    # ── Private Helpers ──────────────────────────────────────────────────

    def _fire_rule(self, rule_id, **kwargs):
        """Find the rule by ID and create an InferenceResult with formatting."""
        rule = next((r for r in self.rules if r["id"] == rule_id), None)
        if rule:
            try:
                message = rule["message"].format(**kwargs)
            except KeyError:
                message = rule["message"]
            self.results.append(InferenceResult(
                rule_id=rule["id"],
                rule_name=rule["name"],
                severity=rule["severity"],
                message=message,
                action=rule["action"],
                category=rule["category"],
            ))

    @staticmethod
    def _is_during_curfew(hour, curfew_start, curfew_end):
        """Check if an hour falls within a curfew window."""
        if curfew_start is None:
            return False
        if curfew_start > curfew_end:
            return hour >= curfew_start or hour < curfew_end
        return curfew_start <= hour < curfew_end
