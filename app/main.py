from fastapi import FastAPI, Depends, HTTPException, status
from app.database import Base, engine, get_db
from app import models, schemas
from typing import List
from sqlalchemy.orm import Session

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
            detail="City not found."
        )
    return city