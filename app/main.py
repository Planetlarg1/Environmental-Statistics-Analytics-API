from fastapi import FastAPI, Depends, HTTPException, status, Query
from app.database import Base, engine, get_db
from app import models, schemas
from typing import List, Optional
from sqlalchemy.orm import Session
from app.station_mappings import station_allowed_for_city, correct_station_for_city

# CONFIG
app = FastAPI(
    title="Environmental Statistics Analytics API",
    description="A RESTful API for environmental and climate statistics across cities.",
    version="0.1.0"
)

Base.metadata.create_all(bind=engine)

# ROUTES
# Root
@app.get("/")
def root():
    return {"message": "Running Environmental Statistics Analytics API"}


# Health check
@app.get("/health")
def health_check():
    return {"status": "ok"}


# POST Cities
@app.post("/cities", response_model=schemas.CityResponse, status_code=status.HTTP_201_CREATED)
def create_city(city: schemas.CityCreate, db: Session = Depends(get_db)):
    # Check if already exists
    existing_city = db.query(models.City).filter(models.City.name == city.name).first()
    if existing_city:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"City {city.name} already exists."
        )
    
    # Add new city
    new_city = models.City(name=city.name)
    db.add(new_city)
    db.commit()
    db.refresh(new_city)
    return new_city


# GET Cities
@app.get("/cities", response_model=List[schemas.CityResponse])
def list_cities(db: Session = Depends(get_db)):
    # Return all cities
    return db.query(models.City).all()


# GET City BY ID
@app.get("/cities/{city_id}", response_model=schemas.CityResponse)
def get_city(city_id: int, db: Session = Depends(get_db)):
    # Index city by ID and return
    city = db.query(models.City).filter(models.City.id == city_id).first()
    # Check exists
    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"City with id {city_id} not found."
        )
    return city


# POST Stations
@app.post("/stations", response_model=schemas.StationResponse, status_code=status.HTTP_201_CREATED)
def create_station(station: schemas.StationCreate, db: Session = Depends(get_db)):
    # Check for associated city
    city = db.query(models.City).filter(models.City.id == station.city_id).first()
    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provided city id {station.city_id} for station {station.name} not found."
        )
    
    # Check station to city mapping
    if not station_allowed_for_city(city.name, station.name):
        correct_station = correct_station_for_city(city.name)

        if correct_station:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{station.name} is not the approved station for {city.name}. The allowed station is {correct_station}."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No approved station mapping exists for {city.name}."
            )    

    # Check already exists
    existing_station = db.query(models.Station).filter(models.Station.name == station.name).first()
    if existing_station:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Station {station.name} already exists."
        )

    # Create new station
    new_station = models.Station(
        name=station.name,
        city_id=station.city_id,
        latitude=station.latitude,
        longitude=station.longitude
    )
    db.add(new_station)
    db.commit()
    db.refresh(new_station)
    return new_station


# GET Stations (by city)
@app.get("/stations", response_model=List[schemas.StationResponse])
def list_stations(
    city_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db)
):
    query = db.query(models.Station)

    # Filter by city if specified
    if city_id is not None:
        query = query.filter(models.Station.city_id == city_id)

    return query.all()


# GET Station BY ID
@app.get("/stations/{station_id}", response_model=schemas.StationResponse)
def get_station(station_id: int, db: Session = Depends(get_db)):
    # Index station by ID and return
    station = db.query(models.Station).filter(models.Station.id == station_id).first()
    # Check exists
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station with id {station_id} not found."
        )
    return station