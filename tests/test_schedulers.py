"""Tests for the Flight and Cargo Scheduler modules."""

import pytest
from expert_system.flight_scheduler import FlightScheduler, Flight
from expert_system.cargo_scheduler import CargoScheduler, CargoShipment


class TestFlightScheduler:
    """Tests for FlightScheduler."""

    def setup_method(self):
        self.scheduler = FlightScheduler()

    def test_add_valid_flight(self):
        result = self.scheduler.add_flight(
            flight_number="AS-101",
            aircraft="B777-300ER",
            origin="JFK",
            destination="LHR",
            departure_time="10:00",
            arrival_time="22:00",
        )
        assert "flight" in result
        assert result["flight"]["status"] == "approved"

    def test_add_rejected_flight(self):
        result = self.scheduler.add_flight(
            flight_number="AS-102",
            aircraft="B737-800",
            origin="JFK",
            destination="DXB",
            departure_time="10:00",
            arrival_time="22:00",
        )
        assert result["flight"]["status"] == "rejected"

    def test_get_all_flights(self):
        self.scheduler.add_flight(
            flight_number="AS-103",
            aircraft="B777-300ER",
            origin="JFK",
            destination="LHR",
            departure_time="10:00",
            arrival_time="22:00",
        )
        flights = self.scheduler.get_all_flights()
        assert len(flights) == 1
        assert flights[0]["flight_number"] == "AS-103"

    def test_delete_flight(self):
        self.scheduler.add_flight(
            flight_number="AS-104",
            aircraft="B777-300ER",
            origin="JFK",
            destination="LHR",
            departure_time="10:00",
            arrival_time="22:00",
        )
        flight_id = self.scheduler.flights[0].id
        self.scheduler.delete_flight(flight_id)
        assert len(self.scheduler.get_all_flights()) == 0

    def test_aircraft_conflict_detection(self):
        """Same aircraft, overlapping times should produce a conflict."""
        self.scheduler.add_flight(
            flight_number="AS-201",
            aircraft="B777-300ER",
            origin="JFK",
            destination="LHR",
            departure_time="10:00",
            arrival_time="18:00",
        )
        self.scheduler.add_flight(
            flight_number="AS-202",
            aircraft="B777-300ER",
            origin="LHR",
            destination="FRA",
            departure_time="14:00",
            arrival_time="16:00",
        )
        conflicts = self.scheduler.check_conflicts()
        assert any(c["type"] == "aircraft_conflict" for c in conflicts)

    def test_gate_conflict_detection(self):
        """Same origin within 15 min should produce a gate conflict."""
        self.scheduler.add_flight(
            flight_number="AS-301",
            aircraft="B777-300ER",
            origin="JFK",
            destination="LHR",
            departure_time="10:00",
            arrival_time="22:00",
        )
        self.scheduler.add_flight(
            flight_number="AS-302",
            aircraft="A350-900",
            origin="JFK",
            destination="FRA",
            departure_time="10:10",
            arrival_time="22:00",
        )
        conflicts = self.scheduler.check_conflicts()
        assert any(c["type"] == "gate_conflict" for c in conflicts)

    def test_schedule_summary(self):
        self.scheduler.add_flight(
            flight_number="AS-401",
            aircraft="B777-300ER",
            origin="JFK",
            destination="LHR",
            departure_time="10:00",
            arrival_time="22:00",
        )
        summary = self.scheduler.get_schedule_summary()
        assert summary["total_flights"] == 1
        assert summary["approved"] == 1


class TestCargoScheduler:
    """Tests for CargoScheduler."""

    def setup_method(self):
        self.scheduler = CargoScheduler()

    def test_add_valid_shipment(self):
        result = self.scheduler.add_shipment(
            aircraft="B747-400F",
            origin="JFK",
            destination="LHR",
            cargo_type="general",
            weight_kg=5000,
            volume_m3=20,
            is_passenger_flight=False,
        )
        assert "shipment" in result
        assert result["shipment"]["status"] == "approved"

    def test_add_rejected_shipment(self):
        result = self.scheduler.add_shipment(
            aircraft="B777-300ER",
            origin="JFK",
            destination="LHR",
            cargo_type="hazardous",
            weight_kg=600,
            volume_m3=10,
            is_passenger_flight=True,
        )
        assert result["shipment"]["status"] == "rejected"

    def test_auto_transit_estimation(self):
        """Transit hours auto-estimated when not provided."""
        result = self.scheduler.add_shipment(
            aircraft="B747-400F",
            origin="JFK",
            destination="LHR",
            cargo_type="general",
            weight_kg=1000,
            volume_m3=5,
            is_passenger_flight=False,
            estimated_transit_hours=0,
        )
        assert result["shipment"]["estimated_transit_hours"] > 0

    def test_get_all_shipments(self):
        self.scheduler.add_shipment(
            aircraft="B747-400F",
            origin="JFK",
            destination="LHR",
            cargo_type="general",
            weight_kg=1000,
            volume_m3=5,
            is_passenger_flight=False,
        )
        shipments = self.scheduler.get_all_shipments()
        assert len(shipments) == 1

    def test_delete_shipment(self):
        self.scheduler.add_shipment(
            aircraft="B747-400F",
            origin="JFK",
            destination="LHR",
            cargo_type="general",
            weight_kg=1000,
            volume_m3=5,
            is_passenger_flight=False,
        )
        sid = self.scheduler.shipments[0].id
        self.scheduler.delete_shipment(sid)
        assert len(self.scheduler.get_all_shipments()) == 0

    def test_cargo_summary(self):
        self.scheduler.add_shipment(
            aircraft="B747-400F",
            origin="JFK",
            destination="LHR",
            cargo_type="general",
            weight_kg=5000,
            volume_m3=20,
            is_passenger_flight=False,
        )
        summary = self.scheduler.get_cargo_summary()
        assert summary["total_shipments"] == 1
        assert summary["total_weight_kg"] == 5000

    def test_optimize_loading(self):
        self.scheduler.add_shipment(
            aircraft="B747-400F",
            origin="JFK",
            destination="LHR",
            cargo_type="general",
            weight_kg=5000,
            volume_m3=20,
            is_passenger_flight=False,
        )
        plan = self.scheduler.optimize_loading("B747-400F")
        assert "loaded_shipments" in plan
        assert plan["aircraft"] == "B747-400F"

    def test_optimize_loading_unknown_aircraft(self):
        plan = self.scheduler.optimize_loading("UNKNOWN")
        assert "error" in plan
