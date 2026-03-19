import os
import sys
import pandas as pd

# Allow imports from parent dir
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.models import Observation, Station

STATIONS = {
    "heathrow",
    "ringway",
    "shawbury",
    "bradford",
    "sheffield",
    "cambridge",
    "oxford",
    "yeovilton",
    "cardiff",
    "leuchars",
    "paisley",
    "armagh"
}

START_YEAR = 1960

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "MET Office Weather Data.csv")

def main():
    # Load csv
    df = pd.read_csv(CSV_PATH)

    # Filter down years and stations
    df = df[
        (df["station"].isin(STATIONS)) &
        (df["year"] >= START_YEAR)
    ]

    print(f"Number of filtered rows: {len(df)}")

    db = SessionLocal()

    try:
        # Build lookup table from station name in DB -> station_id
        stations = db.query(Station).all()
        station_lookup = {station.name.lower(): station.id for station in stations}

        inserted = 0
        skipped = 0

        # Iterate through rows and
        for _, row in df.iterrows():
            station_name = row["station"].strip().lower()
            station_id = station_lookup.get(station_name)

            # Skip rows for stations not yet inserted into DB
            if station_id is None:
                skipped += 1
                continue

            year = int(row["year"])
            month = int(row["month"])

            # Skip duplicates if already imported
            existing = (
                db.query(Observation)
                .filter(
                    Observation.station_id == station_id,
                    Observation.year == year,
                    Observation.month == month
                )
                .first()
            )

            if existing:
                skipped += 1
                continue

            # Create new observation and add to DB
            observation = Observation(
                station_id = station_id,
                year = year,
                month = month, 
                tmax = None if (pd.isna(row["tmax"]) or row["tmax"] == "NA") else float(row["tmax"]),
                tmin = None if (pd.isna(row["tmin"]) or row["tmin"] == "NA") else float(row["tmin"]),
                af = None if (pd.isna(row["af"]) or row["af"] == "NA") else float(row["af"]),
                rain = None if (pd.isna(row["rain"]) or row["rain"] == "NA") else float(row["rain"]),
                sun = None if (pd.isna(row["sun"]) or row["sun"] == "NA") else float(row["sun"])                    
            )

            db.add(observation)
            inserted += 1

        db.commit()

        print(f"Inserted: {inserted} observations")
        print(f"Skipped: {skipped} observations")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()