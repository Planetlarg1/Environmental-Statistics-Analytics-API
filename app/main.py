from fastapi import FastAPI, Depends, HTTPException, status, Query
from app.database import Base, engine, get_db
from app import models, schemas
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.station_mappings import station_allowed_for_city, correct_station_for_city
from app.auth import check_creds, gen_access_token, get_current_admin, hash_password

# CONFIG
app = FastAPI(
    title="Environmental Statistics Analytics API",
    description="A RESTful API for environmental and climate statistics across cities.",
    version="0.1.0"
)

Base.metadata.create_all(bind=engine)

#################
# SYSTEM ROUTES #
#################

# Root
@app.get("/")
def root():
    return {"message": "Running Environmental Statistics Analytics API"}


# Health check
@app.get("/health")
def health_check():
    return {"status": "ok"}


#################
# CITIES ROUTES #
#################

# POST Cities
@app.post("/cities", response_model=schemas.CityResponse, status_code=status.HTTP_201_CREATED)
def create_city(city: schemas.CityCreate, db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
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


# PUT City by ID
@app.put("/cities/{city_id}", response_model=schemas.CityResponse)
def update_city(city_id: int, city_update: schemas.CityUpdate, db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    city = db.query(models.City).filter(models.City.id == city_id).first()
    # Check valid id
    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"City with id {city_id} not found."
        )
    
    # Check if new name is already taken
    existing_city = (
        db.query(models.City)
        .filter(models.City.name ==  city_update.name, models.City.id != city_id)
        .first()
    )
    if existing_city:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Another city already exists with the name {city_update.name}."
        )
    
    city.name = city_update.name
    db.commit()
    db.refresh(city)
    return city
    

# DELETE City BY ID
@app.delete("/cities/{city_id}", status_code=status.HTTP_200_OK)
def delete_city(city_id: int, db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    city = db.query(models.City).filter(models.City.id == city_id).first()
    # Check if city exists
    if not city:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"City with id {city_id} not found."
        )
    
    # Check for dependencies
    if city.stations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete city {city.name} while it has dependencies."
        )
    
    db.delete(city)
    db.commit()
    return {"message": f"City {city.name} has been successfully deleted."}


###################
# STATIONS ROUTES #
###################

# POST Stations
@app.post("/stations", response_model=schemas.StationResponse, status_code=status.HTTP_201_CREATED)
def create_station(station: schemas.StationCreate, db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
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


# PUT Station BY ID
@app.put("/stations/{station_id}", response_model=schemas.StationResponse)
def update_station(station_id: int, station_update: schemas.StationUpdate, db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    station = db.query(models.Station).filter(models.Station.id == station_id).first()
    # Check valid id
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station with id {station_id} not found."
        )
    
    # Check valid city_id
    city = db.query(models.City).filter(models.City.id == station_update.city_id).first()
    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"City with id {station_update.city_id} not found."
        )
    
    # Check valid station -> city mapping
    if not station_allowed_for_city(city.name, station_update.name):
        correct_station = correct_station_for_city(city.name)

        if correct_station:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{station_update.name} is not the approved station for {city.name}. The allowed station is {correct_station}."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No approved station mapping exists for {city.name}."
            )
        
    # Check already exists
    existing_station = (
        db.query(models.Station)
        .filter(models.Station.name == station_update.name, models.Station.id != station_id)
        .first()
    )
    if existing_station:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Another station already exists with the name {station_update.name}."
        )

    # Update station
    station.name = station_update.name
    station.city_id = station_update.city_id
    station.latitude = station_update.latitude
    station.longitude = station_update.longitude

    db.commit()
    db.refresh(station)
    return station


# DELETE Station BY ID
@app.delete("/stations/{station_id}", status_code=status.HTTP_200_OK)
def delete_station(station_id: int, db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    station = db.query(models.Station).filter(models.Station.id == station_id).first()
    # Check exists
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station with id {station_id} not found."
        )
    
    # Check for dependencies
    if station.observations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete station {station.name} while it has dependencies."
        )

    # Delete station 
    db.delete(station)
    db.commit()
    return {"message": f"Station {station.name} has been successfully deleted."}


#######################
# OBSERVATIONS ROUTES #
#######################

# POST Observations
@app.post("/observations", response_model=schemas.ObservationCreate, status_code=status.HTTP_201_CREATED)
def create_observation(observation: schemas.ObservationCreate, db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    # Check station exists
    station = db.query(models.Station).filter(models.Station.id == observation.station_id).first()
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station with id {observation.station_id} not found."
        )
    
    # Sanitise Month
    if observation.month < 1 or observation.month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid month index {observation.month}."
        )
    
    # Prevent Duplicate station/year/month combination
    existing_observation = (
        db.query(models.Observation)
        .filter(
            models.Observation.station_id == observation.station_id,
            models.Observation.year == observation.year,
            models.Observation.month == observation.month
        )
        .first()
    )
    if existing_observation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The observation for {observation.month}/{observation.year} from station {observation.station_id} already exists."
        )
    
    # Add new observation
    new_observation = models.Observation(
        station_id = observation.station_id,
        year = observation.year,
        month = observation.month,
        tmax = observation.tmax,
        tmin = observation.tmin,
        af = observation.af,
        rain = observation.rain,
        sun = observation.sun
    )

    db.add(new_observation)
    db.commit()
    db.refresh(new_observation)
    return new_observation


# GET Observations (by city, by start/end year/month)
@app.get("/observations", response_model=List[schemas.ObservationResponse])
def get_observations(
        # Filters
        city_id: Optional[int] = None,
        start_year: Optional[int] = None,
        start_month: Optional[int] = None,
        end_year: Optional[int] = None,
        end_month: Optional[int] = None,
        db: Session = Depends(get_db)
):
    # If month is given then year is required
    if ((start_month is not None and start_year is None)
        or (end_month is not None and end_year is None)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot filter by month without providing a year."
        )
    
    # Validate month ranges
    if ((start_month is not None and (start_month < 1 or start_month > 12)) 
        or (end_month is not None and (end_month < 1 or end_month > 12))):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid month index."
        )
    
    # Check start before end
    if start_year is not None and end_year is not None:
        if (start_year > end_year):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must come before end date."
            )
        elif ((start_year == end_year) 
            and (start_month is not None and end_month is not None)
            and (start_month > end_month)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must come before end date."
            )
    
    # Check city exists
    if city_id is not None:
        city = db.query(models.City).filter(models.City.id == city_id).first()
        if not city:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"City with id {city_id} not found"
            )
        
    query = db.query(models.Observation).join(models.Station)

    # Filter by City
    if city_id is not None:
        query = query.filter(models.Station.city_id == city_id)

    # Filter by start date
    if start_year is not None:
        if start_month is not None:
            query = query.filter(
                (models.Observation.year > start_year) |
                (
                    (models.Observation.year == start_year) &
                    (models.Observation.month >= start_month)
                )
            )
        else:
            query = query.filter(models.Observation.year >= start_year)

    # Filter by end date
    if end_year is not None:
        if end_month is not None:
            query = query.filter(
                (models.Observation.year < end_year) |
                (
                    (models.Observation.year == end_year) &
                    (models.Observation.month <= end_month)
                )
            )
        else:
            query = query.filter(models.Observation.year <= end_year)

    # Run query and return
    results = query.all()
    return results


# GET Observation BY ID
@app.get("/observations/{observation_id}", response_model=schemas.ObservationResponse)
def get_observation(observation_id: int, db: Session = Depends(get_db)):
    observation = (
        db.query(models.Observation)
        .filter(models.Observation.id == observation_id)
        .first()
    )

    # Check exists
    if not observation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Observation with id {observation_id} not found."
        )
    
    return observation


# PUT Observation BY ID
@app.put("/observations/{observation_id}", response_model=schemas.ObservationUpdate)
def update_observation(observation_id: int, observation_update: schemas.ObservationUpdate, db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    observation = (
        db.query(models.Observation)
        .filter(models.Observation.id == observation_id)
        .first()
    )

    # Check exists
    if not observation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Observation with id {observation_id} not found."
        )
    
    # Check that the station exists
    station = db.query(models.Station).filter(models.Station.id == observation_update.station_id).first()
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station with id {observation_update.station_id} not found."
        )
    
    # Validate month
    if observation_update.month < 1 or observation_update.month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Month index {observation_update.month} invalid."
        )
    
    # Prevent year/month/station duplicate
    existing_observation = (
        db.query(models.Observation)
        .filter(
            models.Observation.station_id == observation_update.station_id,
            models.Observation.year == observation_update.year,
            models.Observation.month == observation_update.month,
            models.Observation.id != observation_id
        )
        .first()
    )
    if existing_observation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The observation for {observation_update.month}/{observation_update.year} from station {observation_update.station_id} already exists."
        )
    
    # Create new observation and add to DB
    observation.station_id = observation_update.station_id
    observation.year = observation_update.year
    observation.month = observation_update.month
    observation.tmax = observation_update.tmax
    observation.tmin = observation_update.tmin
    observation.af = observation_update.af
    observation.rain = observation_update.rain
    observation.sun = observation_update.sun

    db.commit()
    db.refresh(observation)
    return observation


# DELETE Observation By ID
@app.delete("/observations/{observation_id}", status_code=status.HTTP_200_OK)
def delete_observation(observation_id: int, db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    observation = (
        db.query(models.Observation)
        .filter(models.Observation.id == observation_id)
        .first()
    )

    # Check if exists
    if not observation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Observation with id {observation_id} not found."
        )
    
    # Delete observation
    db.delete(observation)
    db.commit()

    return {"message": f"Observation with id {observation_id} has been successfully deleted."}


###############
# AUTH ROUTES #
###############

# Admin Login
@app.post("/admin_login", response_model=schemas.TokenResponse)
def admin_login(admin_creds: schemas.AdminLogin, db: Session = Depends(get_db)):
    admin = check_creds(admin_creds.username, admin_creds.password, db)

    # Check exists
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )
    
    access_token = gen_access_token(data={"sub": admin.username})

    # Return authorising token, allowing access to locked endpoints
    return {"access_token": access_token, "token_type": "bearer"}


# Admin Register - requires already logged in admin
@app.post("/admin_register", response_model=schemas.AdminResponse, status_code=status.HTTP_201_CREATED)
def create_admin(
    admin_data: schemas.AdminCreate,
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin)
):
    # Check if username is taken
    existing_admin = db.query(models.Admin).filter(models.Admin.username == admin_data.username).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username {admin_data.username} is taken."
        )
    
    # Create and add new admin to db
    new_admin= models.Admin(
        username=admin_data.username,
        password_hash=hash_password(admin_data.password)
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return new_admin


# GET admins
@app.get("/admins", response_model=List[schemas.AdminResponse])
def list_admins(
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin)
):
    return db.query(models.Admin).all()


####################
# ANALYTICS ROUTES #
####################

# GET Summary - Returns no. observations and avg of data across an optional given time range for a given city
@app.get("/cities/{city_id}/summary", response_model=schemas.CitySummaryResponse)
def get_city_summary(
    city_id: int,
    # Optional time range filters
    start_year: Optional[int] = None,
    start_month: Optional[int] = None,
    end_year: Optional[int] = None,
    end_month: Optional[int] = None,
    db: Session = Depends(get_db)
):
    # Check city exists
    city = db.query(models.City).filter(models.City.id == city_id).first()
    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"City with id {city_id} not found"
        )
        
    # If month is given then year is required
    if ((start_month is not None and start_year is None)
        or (end_month is not None and end_year is None)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot filter by month without providing a year."
        )
    
    # Validate month ranges
    if ((start_month is not None and (start_month < 1 or start_month > 12)) 
        or (end_month is not None and (end_month < 1 or end_month > 12))):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid month index."
        )
    
    # Check start before end
    if start_year is not None and end_year is not None:
        if (start_year > end_year):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must come before end date."
            )
        elif ((start_year == end_year) 
            and (start_month is not None and end_month is not None)
            and (start_month > end_month)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must come before end date."
            )
        
    # Calculate summary data and filter by city_id
    query = (
        db.query(
            func.count(models.Observation.id),
            func.avg(models.Observation.tmax),
            func.avg(models.Observation.tmin),
            func.avg(models.Observation.af),
            func.avg(models.Observation.rain),
            func.avg(models.Observation.sun)
        )
        .join(models.Station, models.Observation.station_id == models.Station.id)
        .filter(models.Station.city_id == city_id)
    )

    # Filter by start date
    if start_year is not None:
        if start_month is not None:
            query = query.filter(
                (models.Observation.year > start_year) |
                (
                    (models.Observation.year == start_year) &
                    (models.Observation.month >= start_month)
                )
            )
        else:
            query = query.filter(models.Observation.year >= start_year)

    # Filter by end date
    if end_year is not None:
        if end_month is not None:
            query = query.filter(
                (models.Observation.year < end_year) |
                (
                    (models.Observation.year == end_year) &
                    (models.Observation.month <= end_month)
                )
            )
        else:
            query = query.filter(models.Observation.year <= end_year)

    # Return summary data
    summary = query.first()

    observation_count, avg_tmax, avg_tmin, avg_af, avg_rain, avg_sun = summary

    return {
        "city_id": city.id,
        "city_name": city.name,
        "observation_count": observation_count,
        "avg_tmax": round(avg_tmax, 2) if isinstance(avg_tmax, float) else None,
        "avg_tmin": round(avg_tmin, 2) if isinstance(avg_tmin, float) else None,
        "avg_af": round(avg_af, 2) if isinstance(avg_af, float) else None,
        "avg_rain": round(avg_rain, 2) if isinstance(avg_rain, float) else None,
        "avg_sun": round(avg_sun, 2) if isinstance(avg_sun, float) else None
    }


# GET Trends - Returns yearly avg per year over a given timeframe for a given metric in a city
@app.get("/cities/{city_id}/trends", response_model=schemas.CityTrendResponse)
def get_trends(
    city_id: int,
    metric: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    # Check city exists
    city = db.query(models.City).filter(models.City.id == city_id).first()
    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"City with id {city_id} not found."
        )
    
    # Check metric
    valid_metrics = {
        "tmax": models.Observation.tmax,
        "tmin": models.Observation.tmin,
        "af": models.Observation.af,
        "rain": models.Observation.rain,
        "sun": models.Observation.sun
    }

    if metric not in valid_metrics:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{metric} is not a valid metric."
        )
    
    # Check start before end
    if (start_year is not None and end_year is not None
        and (start_year > end_year)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start year must come before end year."
        )
    
    # Filter for metrics and city
    metric_column = valid_metrics[metric]

    query = (
        db.query(
            models.Observation.year,
            func.avg(metric_column).label("value")
        )
        .join(models.Station, models.Observation.station_id == models.Station.id)
        .filter(models.Station.city_id == city_id)
    )

    # Filter by start year
    if start_year is not None:
        query = query.filter(models.Observation.year >= start_year)
    
    # Filter by end year
    if end_year is not None:
        query = query.filter(models.Observation.year <= end_year)

    # Group by year, average, and sort
    results = (
        query.group_by(models.Observation.year)
        .order_by(models.Observation.year)
        .all()
    )

    # Set trend points
    trend_points = [{"year": year, "value": round(value, 2) if isinstance(value, float) else None} for year, value in results]

    return {
        "city_id": city.id,
        "city_name": city.name,
        "metric": metric,
        "trend_points": trend_points
    }


# GET Anomalies - Returns years and values where a given metric is far from the mean in a given optional timeframe in a given city
@app.get("/cities/{city_id}/anomalies", response_model=schemas.CityAnomaliesResponse)
def get_city_anomalies(
    city_id: int,
    metric: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    threshold_sd = 2.0

    # Check city exists
    city = db.query(models.City).filter(models.City.id == city_id).first()
    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"City with id {city_id} not found."
        )
    
    # Check metric
    valid_metrics = {
        "tmax": models.Observation.tmax,
        "tmin": models.Observation.tmin,
        "af": models.Observation.af,
        "rain": models.Observation.rain,
        "sun": models.Observation.sun
    }

    if metric not in valid_metrics:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{metric} is not a valid metric."
        )
    
    # Check start before end
    if (start_year is not None and end_year is not None
        and (start_year > end_year)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start year must come before end year."
        )
    
    metric_column = valid_metrics[metric]

    # Calculate average data and filter by city_id
    query = (
        db.query(
            models.Observation.year,
            func.avg(metric_column).label("yearly_average")
        )
        .join(models.Station, models.Observation.station_id == models.Station.id)
        .filter(models.Station.city_id == city_id)
    )

    # Filter by start year
    if start_year is not None:
        query = query.filter(models.Observation.year >= start_year)
    
    # Filter by end year
    if end_year is not None:
        query = query.filter(models.Observation.year <= end_year)

    # Calculate yearly results
    yearly_results = (
        query.group_by(models.Observation.year)
        .order_by(models.Observation.year)
        .all()
    )

    # Remove unusable non-numeric values
    points = [
        {"year": year, "value": float(value)}
        for year, value in yearly_results
        if value is not None
    ]

    # No usable data
    if not points:
        return {
            "city_id": city.id,
            "city_name": city.name,
            "metric": metric,
            "threshold_sd": threshold_sd,
            "anomaly_count": 0,
            "anomalies": []
        }
    
    # Calculate baseline mean
    values = [point["value"] for point in points]
    mean_value = sum(values) / len(values)

    # Calculate standard deviation
    sd = (sum((value - mean_value) ** 2 for value in values) / len(values)) ** 0.5

    anomalies = []

    # Calculate anomalies
    threshold_distance = threshold_sd * sd
    for point in points:
        difference = point["value"] - mean_value

        if abs(difference) >= threshold_distance:
            anomalies.append({
                "year": point["year"],
                "yearly_average": round(point["value"], 2) if isinstance(point["value"], float) else None,
                "baseline_average": round(mean_value, 2) if isinstance(mean_value, float) else None,
                "difference_from_mean": round(difference, 2) if isinstance(difference, float) else None
            })

    return {
        "city_id": city.id,
        "city_name": city.name,
        "metric": metric,
        "threshold_sd": threshold_sd,
        "anomaly_count": len(anomalies),
        "anomalies": anomalies
    }


# GET Comparison - Returns averages and difference for a metric between two cities in a given time range
@app.get("/compare", response_model=schemas.CityComparisonResponse)
def compare_cities(
    city_a_id: int,
    city_b_id: int,
    metric: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    # Check cities exists
    city_a = db.query(models.City).filter(models.City.id == city_a_id).first()
    if not city_a:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"City with id {city_a_id} not found."
        )
    
    city_b = db.query(models.City).filter(models.City.id == city_b_id).first()
    if not city_b:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"City with id {city_b_id} not found."
        )
    
    # Check metric
    valid_metrics = {
        "tmax": models.Observation.tmax,
        "tmin": models.Observation.tmin,
        "af": models.Observation.af,
        "rain": models.Observation.rain,
        "sun": models.Observation.sun
    }

    if metric not in valid_metrics:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{metric} is not a valid metric."
        )
    
    # Check start before end
    if (start_year is not None and end_year is not None
        and (start_year > end_year)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start year must come before end year."
        )
    
    metric_column = valid_metrics[metric]

    # Helper function for comparison endpoint - calc count and avgs
    def get_city_metric_summary(city_id: int):
        query = (
            db.query(
                func.count(models.Observation.id),
                func.avg(metric_column)
            )
            .join(models.Station, models.Observation.station_id == models.Station.id)
            .filter(models.Station.city_id == city_id)
        )

        # Filter by start year
        if start_year is not None:
            query = query.filter(models.Observation.year >= start_year)
        
        # Filter by end year
        if end_year is not None:
            query = query.filter(models.Observation.year <= end_year)

        return query.first()
    
    city_a_count, city_a_avg = get_city_metric_summary(city_a_id)
    city_b_count, city_b_avg = get_city_metric_summary(city_b_id)

    difference = None
    if city_a_avg is not None and city_b_avg is not None:
        difference = city_a_avg - city_b_avg

    return {
        "metric": metric,
        "start_year": start_year,
        "end_year": end_year,
        "city_a": {
            "city_id": city_a.id,
            "city_name": city_a.name,
            "observation_count": city_a_count,
            "average": round(city_a_avg, 2) if isinstance(city_a_avg, float) else None
        },
        "city_b": {
            "city_id": city_b.id,
            "city_name": city_b.name,
            "observation_count": city_b_count,
            "average": round(city_b_avg, 2) if isinstance(city_b_avg, float) else None
        },
        "difference": abs(round(difference, 2)) if isinstance(difference, float) else None
    }