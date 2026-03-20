from sqlalchemy import Column, ForeignKey, Integer, String, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class City(Base):
    __tablename__ = "cities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    stations = relationship("Station", back_populates="city")

class Station(Base):
    __tablename__ = "stations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    latitude = Column(String, nullable=True)
    longitude = Column(String, nullable=True)
    city = relationship("City", back_populates="stations")
    observations = relationship("Observation", back_populates="station")

class Observation(Base):
    __tablename__ = "observations"
    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    tmax = Column(Float, nullable=True)
    tmin = Column(Float, nullable=True)
    af = Column(Float, nullable=True)
    rain = Column(Float, nullable=True)
    sun = Column(Float, nullable=True)
    station = relationship("Station", back_populates="observations")
    __table_args__ = (
        UniqueConstraint("station_id", "year", "month", name="uq_station_year_month"),
    )

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)