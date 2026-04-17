"""
SQLAlchemy database models for the Airline Scheduling Expert System.

Provides persistent storage for flights, cargo shipments, and users.
"""

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for authentication."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)

    flights = db.relationship("FlightRecord", backref="user", lazy=True)
    shipments = db.relationship("CargoRecord", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class FlightRecord(db.Model):
    """Persisted flight schedule record."""

    __tablename__ = "flights"

    id = db.Column(db.Integer, primary_key=True)
    flight_number = db.Column(db.String(20), nullable=False)
    aircraft = db.Column(db.String(20), nullable=False)
    origin = db.Column(db.String(10), nullable=False)
    destination = db.Column(db.String(10), nullable=False)
    departure_time = db.Column(db.String(10), nullable=False)
    arrival_time = db.Column(db.String(10), nullable=False)
    turnaround_time_min = db.Column(db.Integer, nullable=True)
    crew_duty_hours = db.Column(db.Float, nullable=True)
    crew_rest_hours = db.Column(db.Float, nullable=True)
    connection_time_min = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default="scheduled")
    validation_json = db.Column(db.Text, default="[]")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<Flight {self.flight_number}>"


class CargoRecord(db.Model):
    """Persisted cargo shipment record."""

    __tablename__ = "cargo_shipments"

    id = db.Column(db.Integer, primary_key=True)
    shipment_number = db.Column(db.String(20), nullable=False)
    aircraft = db.Column(db.String(20), nullable=False)
    origin = db.Column(db.String(10), nullable=False)
    destination = db.Column(db.String(10), nullable=False)
    cargo_type = db.Column(db.String(20), nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
    volume_m3 = db.Column(db.Float, nullable=False)
    is_passenger_flight = db.Column(db.Boolean, default=True)
    estimated_transit_hours = db.Column(db.Float, default=0)
    description = db.Column(db.Text, default="")
    status = db.Column(db.String(20), default="pending")
    validation_json = db.Column(db.Text, default="[]")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<Cargo {self.shipment_number}>"
