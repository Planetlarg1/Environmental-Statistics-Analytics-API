from pydantic import BaseModel

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
    latitude: str | None = None # Not required
    longitude: str | None = None # Not required

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
    tmax: float | None # Not required
    tmin: float | None # Not required
    af: float | None # Not required
    rain: float | None # Not required
    sun: float | None # Not required

class ObservationCreate(ObservationBase):
    pass

class ObservationUpdate(ObservationBase):
    pass

class ObservationResponse(ObservationBase):
    id: int

    class Config:
        from_attributes = True


# USERS
class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True