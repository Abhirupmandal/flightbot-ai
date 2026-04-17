"""Tests for the Flask application routes and database integration."""

import json
import pytest
from expert_system.models import db, User, FlightRecord, CargoRecord


def _create_test_app():
    """Create a fresh Flask app configured for testing with an in-memory DB.

    This avoids the problem of Flask-SQLAlchemy caching the engine at
    init_app() time — we create a brand-new app + db binding so the
    in-memory URI is used from the start.
    """
    import os
    from flask import Flask
    from flask_login import LoginManager

    test_app = Flask(
        "app",
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
    )
    test_app.config["TESTING"] = True
    test_app.config["SECRET_KEY"] = "test-secret"
    test_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    test_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    test_app.config["WTF_CSRF_ENABLED"] = False

    db.init_app(test_app)

    lm = LoginManager()
    lm.init_app(test_app)
    lm.login_view = "login"
    lm.login_message_category = "info"

    @lm.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Import the main app module to register routes, then copy them
    import app as main_app_module
    for key, value in main_app_module.app.view_functions.items():
        test_app.view_functions[key] = value
    for rule in main_app_module.app.url_map.iter_rules():
        if rule.endpoint not in test_app.url_map._rules_by_endpoint:
            test_app.add_url_rule(
                rule.rule,
                endpoint=rule.endpoint,
                methods=rule.methods - {"OPTIONS", "HEAD"},
            )

    # Copy context processors and template globals
    test_app.context_processor(
        lambda: {"rules_count": len(main_app_module.EXPERT_RULES)}
    )

    with test_app.app_context():
        db.create_all()

    return test_app


@pytest.fixture
def client():
    """Create a test client with a fresh in-memory database."""
    test_app = _create_test_app()

    with test_app.app_context():
        yield test_app.test_client()
        db.drop_all()


@pytest.fixture
def auth_client(client):
    """Create a test client with an authenticated user."""
    # Register a user
    client.post("/register", data={
        "username": "testuser",
        "email": "test@test.com",
        "password": "password123",
        "confirm_password": "password123",
    }, follow_redirects=True)
    return client


class TestAuthRoutes:
    """Tests for authentication routes."""

    def test_login_page_loads(self, client):
        resp = client.get("/login")
        assert resp.status_code == 200
        assert b"Login" in resp.data

    def test_register_page_loads(self, client):
        resp = client.get("/register")
        assert resp.status_code == 200
        assert b"Register" in resp.data or b"Create" in resp.data

    def test_register_new_user(self, client):
        resp = client.post("/register", data={
            "username": "newuser",
            "email": "new@test.com",
            "password": "password123",
            "confirm_password": "password123",
        }, follow_redirects=True)
        assert resp.status_code == 200
        user = User.query.filter_by(username="newuser").first()
        assert user is not None

    def test_register_duplicate_username(self, client):
        client.post("/register", data={
            "username": "dupuser",
            "email": "dup1@test.com",
            "password": "password123",
            "confirm_password": "password123",
        })
        client.get("/logout", follow_redirects=True)
        resp = client.post("/register", data={
            "username": "dupuser",
            "email": "dup2@test.com",
            "password": "password123",
            "confirm_password": "password123",
        }, follow_redirects=True)
        assert b"already taken" in resp.data

    def test_register_password_mismatch(self, client):
        resp = client.post("/register", data={
            "username": "mismatch",
            "email": "mis@test.com",
            "password": "password123",
            "confirm_password": "different",
        }, follow_redirects=True)
        assert b"do not match" in resp.data

    def test_login_valid_user(self, client):
        client.post("/register", data={
            "username": "loginuser",
            "email": "login@test.com",
            "password": "password123",
            "confirm_password": "password123",
        })
        client.get("/logout", follow_redirects=True)
        resp = client.post("/login", data={
            "username": "loginuser",
            "password": "password123",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_login_invalid_password(self, client):
        client.post("/register", data={
            "username": "wrongpw",
            "email": "wrong@test.com",
            "password": "password123",
            "confirm_password": "password123",
        })
        client.get("/logout", follow_redirects=True)
        resp = client.post("/login", data={
            "username": "wrongpw",
            "password": "wrongpassword",
        }, follow_redirects=True)
        assert b"Invalid" in resp.data

    def test_logout(self, auth_client):
        resp = auth_client.get("/logout", follow_redirects=True)
        assert resp.status_code == 200

    def test_protected_route_redirects(self, client):
        resp = client.get("/", follow_redirects=False)
        assert resp.status_code == 302


class TestPageRoutes:
    """Tests for authenticated page routes."""

    def test_dashboard_loads(self, auth_client):
        resp = auth_client.get("/")
        assert resp.status_code == 200
        assert b"Dashboard" in resp.data

    def test_flights_page_loads(self, auth_client):
        resp = auth_client.get("/flights")
        assert resp.status_code == 200
        assert b"Flight Scheduling" in resp.data

    def test_cargo_page_loads(self, auth_client):
        resp = auth_client.get("/cargo")
        assert resp.status_code == 200
        assert b"Cargo Scheduling" in resp.data

    def test_knowledge_page_loads(self, auth_client):
        resp = auth_client.get("/knowledge")
        assert resp.status_code == 200
        assert b"Knowledge Base" in resp.data

    def test_analytics_page_loads(self, auth_client):
        resp = auth_client.get("/analytics")
        assert resp.status_code == 200
        assert b"Analytics" in resp.data


class TestFlightAPI:
    """Tests for flight scheduling API."""

    def test_add_flight(self, auth_client):
        resp = auth_client.post("/api/flights",
            data=json.dumps({
                "flight_number": "AS-001",
                "aircraft": "B777-300ER",
                "origin": "JFK",
                "destination": "LHR",
                "departure_time": "10:00",
                "arrival_time": "22:00",
            }),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["flight"]["status"] == "approved"

    def test_add_flight_missing_field(self, auth_client):
        resp = auth_client.post("/api/flights",
            data=json.dumps({"flight_number": "AS-002"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_add_flight_no_json(self, auth_client):
        resp = auth_client.post("/api/flights", data="not json",
                                  content_type="application/json")
        assert resp.status_code == 400

    def test_delete_flight(self, auth_client):
        auth_client.post("/api/flights",
            data=json.dumps({
                "flight_number": "AS-DEL",
                "aircraft": "B777-300ER",
                "origin": "JFK",
                "destination": "LHR",
                "departure_time": "10:00",
                "arrival_time": "22:00",
            }),
            content_type="application/json",
        )
        rec = FlightRecord.query.first()
        flight_id = rec.id
        resp = auth_client.post(f"/api/flights/{flight_id}/delete",
                                follow_redirects=True)
        assert resp.status_code == 200

    def test_flight_persisted_in_db(self, auth_client):
        auth_client.post("/api/flights",
            data=json.dumps({
                "flight_number": "AS-DB",
                "aircraft": "B777-300ER",
                "origin": "JFK",
                "destination": "LHR",
                "departure_time": "10:00",
                "arrival_time": "22:00",
            }),
            content_type="application/json",
        )
        count = FlightRecord.query.count()
        assert count == 1


class TestCargoAPI:
    """Tests for cargo scheduling API."""

    def test_add_cargo(self, auth_client):
        resp = auth_client.post("/api/cargo",
            data=json.dumps({
                "aircraft": "B747-400F",
                "origin": "JFK",
                "destination": "LHR",
                "cargo_type": "general",
                "weight_kg": 5000,
                "volume_m3": 20,
                "is_passenger_flight": False,
            }),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["shipment"]["status"] == "approved"

    def test_add_cargo_missing_field(self, auth_client):
        resp = auth_client.post("/api/cargo",
            data=json.dumps({"aircraft": "B747-400F"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_cargo_persisted_in_db(self, auth_client):
        auth_client.post("/api/cargo",
            data=json.dumps({
                "aircraft": "B747-400F",
                "origin": "JFK",
                "destination": "LHR",
                "cargo_type": "general",
                "weight_kg": 5000,
                "volume_m3": 20,
                "is_passenger_flight": False,
            }),
            content_type="application/json",
        )
        count = CargoRecord.query.count()
        assert count == 1


class TestExportRoutes:
    """Tests for export functionality."""

    def test_export_flights_csv(self, auth_client):
        resp = auth_client.get("/export/flights/csv")
        assert resp.status_code == 200
        assert resp.content_type == "text/csv; charset=utf-8"

    def test_export_cargo_csv(self, auth_client):
        resp = auth_client.get("/export/cargo/csv")
        assert resp.status_code == 200
        assert resp.content_type == "text/csv; charset=utf-8"

    def test_export_flights_pdf(self, auth_client):
        resp = auth_client.get("/export/flights/pdf")
        assert resp.status_code == 200
        assert resp.content_type == "application/pdf"

    def test_export_cargo_pdf(self, auth_client):
        resp = auth_client.get("/export/cargo/pdf")
        assert resp.status_code == 200
        assert resp.content_type == "application/pdf"

    def test_csv_contains_header_row(self, auth_client):
        resp = auth_client.get("/export/flights/csv")
        lines = resp.data.decode().strip().split("\n")
        assert "Flight Number" in lines[0]


class TestChartDataAPI:
    """Tests for the chart data endpoint."""

    def test_chart_data_endpoint(self, auth_client):
        resp = auth_client.get("/api/chart-data")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "flight_status" in data
        assert "cargo_status" in data
        assert "aircraft_usage" in data

    def test_summary_endpoint(self, auth_client):
        resp = auth_client.get("/api/summary")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "flights" in data
        assert "cargo" in data
