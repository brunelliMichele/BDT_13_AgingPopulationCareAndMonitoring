# db.py
import os
from collections import defaultdict
import numpy as np
import pandas as pd
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

# set postgres connection
def get_db_engine() -> Engine:
    return create_engine(
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

# get all patients from postgres
def get_all_patients():
    engine = get_db_engine()
    query = "SELECT id, first, middle, last, city, birthdate, lat, lon FROM patients"
    df = pd.read_sql(query, con=engine)
    return [
        {
            "id": row["id"],
            "name": row["first"],
            "middlename": row["middle"],
            "surname": row["last"],
            "city": row["city"],
            "birthdate": row["birthdate"],
            "lat": row["lat"],
            "lon": row["lon"],
            "url": f"/patient/{row['id']}"
        }
        for _, row in df.iterrows()
    ]

# get all city with coordinates
def get_city_avg_coords(patients):
    city_coords = defaultdict(list)
    for p in patients:
        if p.get("city") and p.get("lat") and p.get("lon"):
            try:
                city_coords[p["city"]].append((
                    float(p["lat"]),
                    float(p["lon"])
                ))
            except ValueError:
                continue
    return {
        city: np.mean(coords, axis = 0).tolist()
        for city, coords in city_coords.items()
    }

# get patient from ID
def get_patient_by_id(patient_id):
    engine = get_db_engine()
    query = """
        SELECT id, birthdate, deathdate, gender, birthplace, address,
               city, county, first, middle, last
        FROM patients
        WHERE id = %s
    """
    df = pd.read_sql(query, con=engine, params=(patient_id,))
    if not df.empty:
        patient = df.iloc[0]
        return {
            "id": patient["id"],
            "birthdate": patient["birthdate"],
            "deathdate": patient["deathdate"],
            "gender": patient["gender"],
            "birthplace": patient["birthplace"],
            "address": patient["address"],
            "city": patient["city"],
            "county": patient["county"],
            "name": patient["first"],
            "middlename": patient["middle"],
            "surname": patient["last"]
        }
    return None
    
def get_risk_level_by_id(patient_id):
    engine = get_db_engine()
    query = """
        SELECT risk_level
        FROM vital_signs
        WHERE patient_id = %s AND risk_level IS NOT NULL
        ORDER BY date DESC
        LIMIT 1
    """
    df = pd.read_sql(query, con=engine, params=(patient_id,))
    return float(df.iloc[0]["risk_level"]) if not df.empty else None
    
def get_all_risk_level():
    engine = get_db_engine()
    query = """
        SELECT DISTINCT ON (patient_id) patient_id, risk_level
        FROM vital_signs
        WHERE risk_level IS NOT NULL
        ORDER BY patient_id, date DESC
    """
    df = pd.read_sql(query, con=engine)
    return {str(row["patient_id"]): float(row["risk_level"]) for _, row in df.iterrows()}
    

def get_risk_trend_by_id(patient_id):
    engine = get_db_engine()
    query = """
        SELECT date, risk_level
        FROM vital_signs
        WHERE patient_id = %s
        ORDER BY date ASC
    """
    df = pd.read_sql(query, con=engine, params=(patient_id,))
    df = df.dropna(subset=["risk_level"])
    return {
        "dates": df["date"].astype(str).tolist(),
        "values": df["risk_level"].tolist()
    }

def get_risk_trend_raw(patient_id):
    engine = get_db_engine()
    query = "SELECT date, hr, rr, body_temperature, spo2, gsr, risk_level FROM vital_signs WHERE patient_id = %s ORDER BY date ASC"    
    df = pd.read_sql_query(query, con=engine, params=(patient_id,))
    return df.to_dict(orient="records")

