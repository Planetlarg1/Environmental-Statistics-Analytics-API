from sqlalchemy import Column, ForeignKey, Integer, String
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