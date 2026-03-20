from pydantic import BaseModel
from typing import Optional

# CITIES
class CityBase(BaseModel):
    name: str

class CityCreate(CityBase):
    pass

class CityUpdate(CityBase):
    pass

class CityResponse(CityBase):
    id: int

    class Config:
        from_attributes = True


# STATIONS
class StationBase(BaseModel):
    name: str
    city_id: int
    latitude: Optional[str] = None # Not required
    longitude: Optional[str] = None # Not required

class StationCreate(StationBase):
    pass

class StationUpdate(StationBase):
    pass

class StationResponse(StationBase):
    id: int

    class Config:
        from_attributes = True


# OBSERVATIONS
class ObservationBase(BaseModel):
    station_id: int
    year: int
    month: int
    tmax: Optional[float] = None # Not required
    tmin: Optional[float] = None # Not required
    af: Optional[float] = None # Not required
    rain: Optional[float] = None # Not required
    sun: Optional[float] = None # Not required

class ObservationCreate(ObservationBase):
    pass

class ObservationUpdate(ObservationBase):
    pass

class ObservationResponse(ObservationBase):
    id: int

    class Config:
        from_attributes = True


# ADMINS
class AdminCreate(BaseModel):
    username: str
    password: str

class AdminLogin(BaseModel):
    username: str
    password: str

class AdminResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# ANALYTICS
class CitySummaryResponse(BaseModel):
    city_id: int
    city_name: str
    observation_count: int
    avg_tmax: Optional[float] = None
    avg_tmin: Optional[float] = None
    avg_af: Optional[float] = None
    avg_rain: Optional[float] = None
    avg_sun: Optional[float] = None

class TrendPoint(BaseModel):
    year: int
    value: Optional[float] = None

class CityTrendResponse(BaseModel):
    city_id: int
    city_name: str
    metric: str
    trend_points: list[TrendPoint]