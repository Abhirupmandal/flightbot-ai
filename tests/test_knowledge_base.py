"""Tests for the Knowledge Base module."""

import pytest
from expert_system.knowledge_base import (
    AIRCRAFT_FLEET,
    AIRPORTS,
    CARGO_TYPES,
    EXPERT_RULES,
    SCHEDULING_RULES,
    ROUTE_DISTANCES,
    get_route_distance,
)


class TestAircraftFleet:
    """Tests for aircraft fleet data integrity."""

    def test_fleet_has_six_aircraft(self):
        assert len(AIRCRAFT_FLEET) == 6

    def test_all_aircraft_have_required_fields(self):
        required = [
            "type", "max_range_km", "max_passengers", "cargo_capacity_kg",
            "cargo_volume_m3", "fuel_burn_per_hour_kg", "turnaround_time_min",
            "max_flight_hours_per_day", "category",
        ]
        for code, info in AIRCRAFT_FLEET.items():
            for field in required:
                assert field in info, f"{code} missing field '{field}'"

    def test_aircraft_categories_valid(self):
        valid = {"narrow-body", "wide-body", "freighter"}
        for code, info in AIRCRAFT_FLEET.items():
            assert info["category"] in valid, f"{code} has invalid category"

    def test_freighters_have_zero_passengers(self):
        for code, info in AIRCRAFT_FLEET.items():
            if info["category"] == "freighter":
                assert info["max_passengers"] == 0, f"Freighter {code} has passengers"

    def test_range_values_positive(self):
        for code, info in AIRCRAFT_FLEET.items():
            assert info["max_range_km"] > 0, f"{code} has non-positive range"


class TestAirports:
    """Tests for airport data integrity."""

    def test_airports_count(self):
        assert len(AIRPORTS) == 8

    def test_all_airports_have_required_fields(self):
        required = [
            "name", "city", "country", "timezone", "hub",
            "cargo_facility", "curfew_start", "curfew_end", "peak_hours",
        ]
        for code, info in AIRPORTS.items():
            for field in required:
                assert field in info, f"{code} missing field '{field}'"

    def test_airports_with_curfews(self):
        curfew_airports = [
            code for code, info in AIRPORTS.items()
            if info["curfew_start"] is not None
        ]
        assert len(curfew_airports) >= 2
        assert "LHR" in curfew_airports
        assert "FRA" in curfew_airports

    def test_all_airports_have_cargo_facility(self):
        for code, info in AIRPORTS.items():
            assert info["cargo_facility"] is True


class TestRouteDistances:
    """Tests for route distance data."""

    def test_route_count(self):
        assert len(ROUTE_DISTANCES) == 19

    def test_get_route_distance_forward(self):
        assert get_route_distance("JFK", "LHR") == 5539

    def test_get_route_distance_reverse(self):
        assert get_route_distance("LHR", "JFK") == 5539

    def test_get_route_distance_unknown(self):
        assert get_route_distance("JFK", "XXX") is None

    def test_all_distances_positive(self):
        for route, distance in ROUTE_DISTANCES.items():
            assert distance > 0, f"Route {route} has non-positive distance"


class TestCargoTypes:
    """Tests for cargo type data."""

    def test_cargo_types_count(self):
        assert len(CARGO_TYPES) == 6

    def test_all_types_have_required_fields(self):
        required = [
            "name", "priority", "requires_temp_control", "hazardous",
            "max_transit_hours", "handling_time_min", "description",
        ]
        for type_id, info in CARGO_TYPES.items():
            for field in required:
                assert field in info, f"{type_id} missing field '{field}'"

    def test_hazardous_type_flagged(self):
        assert CARGO_TYPES["hazardous"]["hazardous"] is True

    def test_perishable_requires_temp_control(self):
        assert CARGO_TYPES["perishable"]["requires_temp_control"] is True

    def test_live_animals_max_transit(self):
        assert CARGO_TYPES["live_animals"]["max_transit_hours"] <= 18


class TestExpertRules:
    """Tests for expert rules data."""

    def test_rules_count(self):
        assert len(EXPERT_RULES) >= 15

    def test_all_rules_have_required_fields(self):
        required = ["id", "name", "category", "condition", "action", "message", "severity"]
        for rule in EXPERT_RULES:
            for field in required:
                assert field in rule, f"Rule {rule.get('id', '?')} missing '{field}'"

    def test_rule_ids_unique(self):
        ids = [r["id"] for r in EXPERT_RULES]
        assert len(ids) == len(set(ids)), "Duplicate rule IDs found"

    def test_rule_categories_valid(self):
        valid = {"flight", "crew", "cargo"}
        for rule in EXPERT_RULES:
            assert rule["category"] in valid, (
                f"Rule {rule['id']} has invalid category '{rule['category']}'"
            )


class TestSchedulingRules:
    """Tests for scheduling parameters."""

    def test_crew_duty_limit(self):
        assert SCHEDULING_RULES["max_crew_duty_hours_per_day"] == 14

    def test_crew_rest_minimum(self):
        assert SCHEDULING_RULES["min_crew_rest_hours"] == 10

    def test_hazmat_limit(self):
        assert SCHEDULING_RULES["max_hazmat_per_flight_kg"] == 500

    def test_connection_time(self):
        assert SCHEDULING_RULES["min_connection_time_min"] == 60
