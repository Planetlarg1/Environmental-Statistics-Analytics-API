from pydantic import BaseModel

# CITIES
class CityBase(BaseModel):
    name: str

class CityCreate(CityBase):
    pass

class CityResponse(CityBase):
    id: int

    class Config:
        from_attribute = True

# STATIONS
class StationBase(BaseModel):
    name: str
    city_id: int
    latitude: str | None = None # Not required
    longitude: str | None = None # Not required

class StationCreate(StationBase):
    pass

class StationResponse(StationBase):
    id: int

    class Config:
        from_attribute = True