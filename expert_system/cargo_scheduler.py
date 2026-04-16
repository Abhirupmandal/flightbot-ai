"""
Cargo Scheduler Module.

Manages cargo shipments, validates them against expert rules,
and provides cargo routing and optimization suggestions.
"""

from expert_system.knowledge_base import (
    AIRCRAFT_FLEET,
    AIRPORTS,
    CARGO_TYPES,
    SCHEDULING_RULES,
    get_route_distance,
)
from expert_system.inference_engine import InferenceEngine


class CargoShipment:
    """Represents a single cargo shipment."""

    _next_id = 1

    def __init__(self, shipment_id_prefix, aircraft, origin, destination,
                 cargo_type, weight_kg, volume_m3, is_passenger_flight=True,
                 estimated_transit_hours=0, description=""):
        self.id = CargoShipment._next_id
        CargoShipment._next_id += 1
        self.shipment_number = f"CRG-{self.id:04d}"
        self.aircraft = aircraft
        self.origin = origin
        self.destination = destination
        self.cargo_type = cargo_type
        self.weight_kg = weight_kg
        self.volume_m3 = volume_m3
        self.is_passenger_flight = is_passenger_flight
        self.estimated_transit_hours = estimated_transit_hours
        self.description = description
        self.status = "pending"
        self.validation_results = []

    def to_dict(self):
        cargo_info = CARGO_TYPES.get(self.cargo_type, {})
        aircraft_info = AIRCRAFT_FLEET.get(self.aircraft, {})
        distance = get_route_distance(self.origin, self.destination)

        capacity_kg = aircraft_info.get("cargo_capacity_kg", 0)
        utilization = (self.weight_kg / capacity_kg * 100) if capacity_kg else 0

        return {
            "id": self.id,
            "shipment_number": self.shipment_number,
            "aircraft": self.aircraft,
            "aircraft_type": aircraft_info.get("type", "Unknown"),
            "origin": self.origin,
            "origin_name": AIRPORTS.get(self.origin, {}).get("name", "Unknown"),
            "destination": self.destination,
            "destination_name": AIRPORTS.get(self.destination, {}).get("name", "Unknown"),
            "cargo_type": self.cargo_type,
            "cargo_type_name": cargo_info.get("name", "Unknown"),
            "weight_kg": self.weight_kg,
            "volume_m3": self.volume_m3,
            "is_passenger_flight": self.is_passenger_flight,
            "estimated_transit_hours": self.estimated_transit_hours,
            "description": self.description,
            "distance_km": distance,
            "cargo_utilization_pct": round(utilization, 1),
            "priority": cargo_info.get("priority", 5),
            "handling_time_min": cargo_info.get("handling_time_min", 30),
            "status": self.status,
            "validation_results": [r.to_dict() for r in self.validation_results],
        }


class CargoScheduler:
    """Manages cargo shipments and validates them using the inference engine."""

    def __init__(self):
        self.shipments = []
        self.engine = InferenceEngine()

    def add_shipment(self, aircraft, origin, destination, cargo_type,
                     weight_kg, volume_m3, is_passenger_flight=True,
                     estimated_transit_hours=0, description=""):
        """Add a new cargo shipment and validate it against expert rules."""
        shipment = CargoShipment(
            shipment_id_prefix="CRG",
            aircraft=aircraft,
            origin=origin,
            destination=destination,
            cargo_type=cargo_type,
            weight_kg=weight_kg,
            volume_m3=volume_m3,
            is_passenger_flight=is_passenger_flight,
            estimated_transit_hours=estimated_transit_hours,
            description=description,
        )

        # Auto-estimate transit hours if not provided
        if estimated_transit_hours == 0:
            distance = get_route_distance(origin, destination)
            if distance:
                estimated_transit_hours = round(distance / 850, 1)
                shipment.estimated_transit_hours = estimated_transit_hours

        # Validate through inference engine
        cargo_data = {
            "aircraft": aircraft,
            "origin": origin,
            "destination": destination,
            "cargo_type": cargo_type,
            "weight_kg": weight_kg,
            "volume_m3": volume_m3,
            "is_passenger_flight": is_passenger_flight,
            "estimated_transit_hours": estimated_transit_hours,
        }

        results = self.engine.evaluate_cargo(cargo_data)
        shipment.validation_results = results

        # Set status based on results
        has_critical = any(r.severity == "critical" for r in results)
        has_high = any(r.severity == "high" for r in results)

        if has_critical:
            shipment.status = "rejected"
        elif has_high:
            shipment.status = "warning"
        else:
            shipment.status = "approved"

        self.shipments.append(shipment)

        # Get recommendations
        recommendations = self.engine.get_recommendations(cargo_data=cargo_data)

        return {
            "shipment": shipment.to_dict(),
            "recommendations": recommendations,
        }

    def get_all_shipments(self):
        """Return all cargo shipments."""
        return [s.to_dict() for s in self.shipments]

    def delete_shipment(self, shipment_id):
        """Remove a shipment by ID."""
        self.shipments = [s for s in self.shipments if s.id != shipment_id]

    def get_cargo_summary(self):
        """Return a summary of the current cargo schedule."""
        total = len(self.shipments)
        approved = sum(1 for s in self.shipments if s.status == "approved")
        warning = sum(1 for s in self.shipments if s.status == "warning")
        rejected = sum(1 for s in self.shipments if s.status == "rejected")

        total_weight = sum(s.weight_kg for s in self.shipments)
        total_volume = sum(s.volume_m3 for s in self.shipments)

        type_breakdown = {}
        for s in self.shipments:
            cargo_info = CARGO_TYPES.get(s.cargo_type, {})
            name = cargo_info.get("name", s.cargo_type)
            type_breakdown.setdefault(name, {"count": 0, "weight": 0})
            type_breakdown[name]["count"] += 1
            type_breakdown[name]["weight"] += s.weight_kg

        route_breakdown = {}
        for s in self.shipments:
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

    def optimize_loading(self, aircraft_id):
        """
        Suggest an optimal loading order for approved shipments
        on a given aircraft, based on priority and weight.
        """
        aircraft = AIRCRAFT_FLEET.get(aircraft_id)
        if not aircraft:
            return {"error": f"Aircraft '{aircraft_id}' not found."}

        approved = [s for s in self.shipments if s.status == "approved"]
        # Sort by priority (lower = higher priority), then by weight desc
        approved.sort(key=lambda s: (
            CARGO_TYPES.get(s.cargo_type, {}).get("priority", 5),
            -s.weight_kg,
        ))

        loading_plan = []
        remaining_weight = aircraft["cargo_capacity_kg"]
        remaining_volume = aircraft["cargo_volume_m3"]

        loaded = []
        deferred = []

        for s in approved:
            if s.weight_kg <= remaining_weight and s.volume_m3 <= remaining_volume:
                loaded.append(s.to_dict())
                remaining_weight -= s.weight_kg
                remaining_volume -= s.volume_m3
            else:
                deferred.append(s.to_dict())

        return {
            "aircraft": aircraft_id,
            "aircraft_type": aircraft["type"],
            "max_capacity_kg": aircraft["cargo_capacity_kg"],
            "max_volume_m3": aircraft["cargo_volume_m3"],
            "loaded_shipments": loaded,
            "deferred_shipments": deferred,
            "total_loaded_weight": aircraft["cargo_capacity_kg"] - remaining_weight,
            "total_loaded_volume": aircraft["cargo_volume_m3"] - remaining_volume,
            "remaining_weight": remaining_weight,
            "remaining_volume": remaining_volume,
        }
