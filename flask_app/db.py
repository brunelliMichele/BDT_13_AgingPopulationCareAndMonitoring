# db.py
import os
import psycopg2
from collections import defaultdict
import numpy as np
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# set postgres connection
def get_db_connection():
    try:
        return psycopg2.connect(
            host = DB_HOST,
            port = DB_PORT,
            database = DB_NAME,
            user = DB_USER,
            password = DB_PASSWORD
        )
    except psycopg2.Error as e:
        print(f"❌ DB connection failed: {e}")
        raise

# get all patients from postgres
def get_all_patients():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, first, middle, last, city, birthdate, lat, lon FROM patients")
            rows = cur.fetchall()
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "middlename": row[2],
                    "surname": row[3],
                    "city": row[4],
                    "birthdate": row[5],
                    "lat": row[6],
                    "lon": row[7],
                    "url": f"/patient/{row[0]}"
                }
                for row in rows
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
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, birthdate, deathdate, gender, birthplace, address, city, county, first, middle, last FROM patients WHERE id = %s", (patient_id,))
            patient = cur.fetchone()
            if patient:
                return {
                    "id": patient[0],
                    "birthdate": patient[1],
                    "deathdate": patient[2],
                    "gender": patient[3],
                    "birthplace": patient[4],
                    "address": patient[5],
                    "city": patient[6],
                    "county": patient[7],
                    "name": patient[8],
                    "middlename": patient[9],
                    "surname": patient[10]
                }
            return None