"""
database.py
===========
SQLAlchemy ORM setup for the Smart Home Energy Monitoring System.

Provides:
  - SQLite engine and session factory
  - User, Device, and Appliance models
  - Base declarative base for future models
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# ---------------------------------------------------------------------------
# Engine & Session
# ---------------------------------------------------------------------------
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "energy_monitor.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite + FastAPI
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class User(Base):
    """
    Represents a registered user of the SaaS platform.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    device = relationship("Device", back_populates="owner", uselist=False)
    appliances = relationship("Appliance", back_populates="owner")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Device(Base):
    """
    Represents an ESP32 device claimed by a user.
    One user can claim exactly one device.
    """
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    device_id = Column(String, unique=True, index=True, nullable=False)  # ESP32 MAC or custom ID
    claimed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="device")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "device_id": self.device_id,
            "claimed_at": self.claimed_at.isoformat() if self.claimed_at else None,
        }


class Appliance(Base):
    """
    Represents a household appliance registered by the user during onboarding.
    """
    __tablename__ = "appliances"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    wattage = Column(Float, nullable=False)
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="appliances")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "wattage": self.wattage,
            "quantity": self.quantity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Dependency for FastAPI
# ---------------------------------------------------------------------------
def get_db():
    """Yield a database session for FastAPI dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------
def init_db():
    """Create all tables. Call once at application startup."""
    Base.metadata.create_all(bind=engine)

