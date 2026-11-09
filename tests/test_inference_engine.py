"""Tests for the Inference Engine module."""

import pytest
from expert_system.inference_engine import InferenceEngine, InferenceResult


class TestInferenceResult:
    """Tests for InferenceResult data class."""

    def test_to_dict(self):
        r = InferenceResult("R01", "Test Rule", "critical", "msg", "reject", "flight")
        d = r.to_dict()
        assert d["rule_id"] == "R01"
        assert d["rule_name"] == "Test Rule"
        assert d["severity"] == "critical"
        assert d["message"] == "msg"
        assert d["action"] == "reject"
        assert d["category"] == "flight"


class TestFlightEvaluation:
    """Tests for flight rule evaluation."""

    def setup_method(self):
        self.engine = InferenceEngine()

    def test_valid_flight_passes(self):
        """B777-300ER JFK->LHR should pass (within range)."""
        results = self.engine.evaluate_flight({
            "aircraft": "B777-300ER",
            "origin": "JFK",
            "destination": "LHR",
            "departure_time": "10:00",
            "arrival_time": "22:00",
        })
        assert any(r.rule_id == "OK" for r in results)

    def test_range_exceeded_rejected(self):
        """B737-800 JFK->DXB should be rejected (range 5765 < 11023)."""
        results = self.engine.evaluate_flight({
            "aircraft": "B737-800",
            "origin": "JFK",
            "destination": "DXB",
            "departure_time": "10:00",
            "arrival_time": "22:00",
        })
        assert any(r.rule_id == "R01" for r in results)
        r01 = [r for r in results if r.rule_id == "R01"][0]
        assert r01.severity == "critical"
        assert r01.action == "reject_schedule"

    def test_night_curfew_rejected(self):
        """Departure from LHR at 01:00 should violate curfew (23:00-06:00)."""
        results = self.engine.evaluate_flight({
            "aircraft": "B777-300ER",
            "origin": "LHR",
            "destination": "JFK",
            "departure_time": "01:00",
            "arrival_time": "08:00",
        })
        assert any(r.rule_id == "R03" for r in results)

    def test_crew_duty_exceeded(self):
        """Crew duty of 16 hours should trigger R04 (max 14)."""
        results = self.engine.evaluate_flight({
            "aircraft": "B777-300ER",
            "origin": "JFK",
            "destination": "LHR",
            "departure_time": "10:00",
            "arrival_time": "22:00",
            "crew_duty_hours": 16,
        })
        assert any(r.rule_id == "R04" for r in results)

    def test_crew_rest_insufficient(self):
        """Crew rest of 8 hours should trigger R05 (min 10)."""
        results = self.engine.evaluate_flight({
            "aircraft": "B777-300ER",
            "origin": "JFK",
            "destination": "LHR",
            "departure_time": "10:00",
            "arrival_time": "22:00",
            "crew_rest_hours": 8,
        })
        assert any(r.rule_id == "R05" for r in results)

    def test_turnaround_time_warning(self):
        """Turnaround of 30 min for wide-body should trigger R02 (min 90)."""
        results = self.engine.evaluate_flight({
            "aircraft": "B777-300ER",
            "origin": "JFK",
            "destination": "LHR",
            "departure_time": "10:00",
            "arrival_time": "22:00",
            "turnaround_time_min": 30,
        })
        assert any(r.rule_id == "R02" for r in results)

    def test_connection_time_warning(self):
        """Connection of 30 min should trigger R15 (min 60)."""
        results = self.engine.evaluate_flight({
            "aircraft": "B777-300ER",
            "origin": "JFK",
            "destination": "LHR",
            "departure_time": "10:00",
            "arrival_time": "22:00",
            "connection_time_min": 30,
        })
        assert any(r.rule_id == "R15" for r in results)

    def test_unknown_aircraft_rejected(self):
        results = self.engine.evaluate_flight({
            "aircraft": "UNKNOWN",
            "origin": "JFK",
            "destination": "LHR",
            "departure_time": "10:00",
            "arrival_time": "22:00",
        })
        assert any(r.rule_id == "SYS" for r in results)
        assert results[0].severity == "critical"

    def test_unknown_origin_rejected(self):
        results = self.engine.evaluate_flight({
            "aircraft": "B777-300ER",
            "origin": "XXX",
            "destination": "LHR",
            "departure_time": "10:00",
            "arrival_time": "22:00",
        })
        assert any(r.rule_id == "SYS" for r in results)


class TestCargoEvaluation:
    """Tests for cargo rule evaluation."""

    def setup_method(self):
        self.engine = InferenceEngine()

    def test_valid_cargo_passes(self):
        """General cargo within limits should pass."""
        results = self.engine.evaluate_cargo({
            "aircraft": "B747-400F",
            "origin": "JFK",
            "destination": "LHR",
            "cargo_type": "general",
            "weight_kg": 5000,
            "volume_m3": 20,
            "is_passenger_flight": False,
            "estimated_transit_hours": 8,
        })
        assert any(r.rule_id == "OK" for r in results)

    def test_overweight_cargo_rejected(self):
        """Cargo exceeding capacity should trigger R06."""
        results = self.engine.evaluate_cargo({
            "aircraft": "B737-800",
            "origin": "JFK",
            "destination": "LAX",
            "cargo_type": "general",
            "weight_kg": 10000,
            "volume_m3": 20,
            "is_passenger_flight": True,
            "estimated_transit_hours": 5,
        })
        assert any(r.rule_id == "R06" for r in results)

    def test_hazmat_over_limit_rejected(self):
        """600kg hazmat on passenger flight should trigger R08."""
        results = self.engine.evaluate_cargo({
            "aircraft": "B777-300ER",
            "origin": "JFK",
            "destination": "LHR",
            "cargo_type": "hazardous",
            "weight_kg": 600,
            "volume_m3": 10,
            "is_passenger_flight": True,
            "estimated_transit_hours": 8,
        })
        assert any(r.rule_id == "R08" for r in results)

    def test_perishable_transit_exceeded(self):
        """Perishable with 30 hour transit should trigger R09."""
        results = self.engine.evaluate_cargo({
            "aircraft": "B747-400F",
            "origin": "JFK",
            "destination": "LHR",
            "cargo_type": "perishable",
            "weight_kg": 1000,
            "volume_m3": 10,
            "is_passenger_flight": False,
            "estimated_transit_hours": 30,
        })
        assert any(r.rule_id == "R09" for r in results)

    def test_live_animal_transit_exceeded(self):
        """Live animals with 20 hour transit should trigger R10."""
        results = self.engine.evaluate_cargo({
            "aircraft": "B747-400F",
            "origin": "JFK",
            "destination": "LHR",
            "cargo_type": "live_animals",
            "weight_kg": 500,
            "volume_m3": 10,
            "is_passenger_flight": False,
            "estimated_transit_hours": 20,
        })
        assert any(r.rule_id == "R10" for r in results)

    def test_unknown_cargo_type_rejected(self):
        results = self.engine.evaluate_cargo({
            "aircraft": "B747-400F",
            "origin": "JFK",
            "destination": "LHR",
            "cargo_type": "unknown_type",
            "weight_kg": 100,
            "volume_m3": 1,
            "is_passenger_flight": False,
            "estimated_transit_hours": 5,
        })
        assert any(r.rule_id == "SYS" for r in results)


class TestRecommendations:
    """Tests for the recommendation engine."""

    def setup_method(self):
        self.engine = InferenceEngine()

    def test_flight_recommendations_returned(self):
        recs = self.engine.get_recommendations(
            flight_data={
                "aircraft": "B737-800",
                "origin": "JFK",
                "destination": "LAX",
                "departure_time": "10:00",
                "arrival_time": "16:00",
            }
        )
        assert isinstance(recs, list)

    def test_cargo_recommendations_returned(self):
        recs = self.engine.get_recommendations(
            cargo_data={
                "aircraft": "B747-400F",
                "origin": "JFK",
                "destination": "LHR",
                "cargo_type": "general",
                "weight_kg": 5000,
                "volume_m3": 20,
            }
        )
        assert isinstance(recs, list)
