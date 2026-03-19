# Mapping dict
CITY_TO_STATIONS_MAPPING = {
    "LONDON": "HEATHROW",
    "MANCHESTER": "RINGWAY",
    "BIRMINGHAM": "SHAWBURY",
    "LEEDS": "BRADFORD",
    "SHEFFIELD": "SHEFFIELD",
    "CAMBRIDGE": "CAMBRIDGE",
    "OXFORD": "OXFORD",
    "BRISTOL": "YEOVILTON",
    "CARDIFF": "CARDIFF",
    "EDINBURGH": "LEUCHARS",
    "GLASGOW": "PAISLEY",
    "BELFAST": "ARMAGH"
}


# Check if posted mapping is correct
def station_allowed_for_city(city_name: str, station_name: str) -> bool:
    allowed_station = CITY_TO_STATIONS_MAPPING.get(city_name.upper())
    return allowed_station == station_name.upper()


# Return correct station for city
def correct_station_for_city(city_name: str) -> str | None:
    return CITY_TO_STATIONS_MAPPING.get(city_name.upper())