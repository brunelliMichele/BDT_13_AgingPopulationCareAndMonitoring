from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from kafka import KafkaConsumer
import psycopg2
import os
import json
from collections import defaultdict
import numpy as np
import sys

# create flask app and initialize webSocket
app = Flask(
    __name__,
    static_folder = "static",
    template_folder = "templates"
    )

socket_io = SocketIO(app, cors_allowed_origins = "*")

# 
def smart_data_consumer():
    smart_data_consumer = KafkaConsumer(
        'smart_home_data',
        bootstrap_servers='kafka:9092',
        value_deserializer = lambda m: json.loads(m.decode('utf-8'))
    )

    for message in smart_data_consumer:
        socket_io.emit('smart_data_message', message.value)

def alert_consumer():
    alert_consumer = KafkaConsumer(
        'alert_topic',
        bootstrap_servers='kafka:9092',
        value_deserializer=lambda a: json.loads(a.decode('utf-8'))
    )
    for message in alert_consumer:
        socket_io.emit("new_alert_message", message.value)

# set postgres connection
def get_db_connection():
    return psycopg2.connect(
        host = os.environ.get("DB_HOST", "db"),
        port = 5432,
        database = os.environ.get("DB_NAME", "medicalData"),
        user = os.environ.get("DB_USER", "user"),
        password = os.environ.get("DB_PASSWORD", "password")
    )

# get all patients from postgres
def get_all_patients():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, first, middle, last, city, birthdate, lat, lon FROM patients")
    rows = cur.fetchall()
    patients = []
    for row in rows:
        patients.append({
            "id": row[0],
            "name": row[1],
            "middlename": row[2],
            "surname": row[3],
            "city": row[4],
            "birthdate": row[5],
            "lat": row[6],
            "lon": row[7],
            "url": f"/patient/{row[0]}"
        })
    cur.close()
    conn.close()
    return patients

""" # get all cities from postgres
def get_all_cities():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT city FROM patients WHERE city IS NOT NULL ORDER BY city;")
    rows = cur.fetchall()
    cities = [row[0] for row in rows]

    cur.close()
    conn.close()
    return cities """

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
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, birthdate, deathdate, gender, birthplace, address, city, county, first, middle, last FROM patients WHERE id = %s", (patient_id,))
    patient = cur.fetchone()

    cur.close()
    conn.close()

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

# set route for main page
@app.route("/")
def index():
    patients = get_all_patients()
    city_coords = get_city_avg_coords(patients)
    cities = sorted(city_coords.keys())

    return render_template("index.html", patients=patients, city_coords=city_coords, cities=cities)

# set route for patient detail page
@app.route("/patient/<string:patient_id>")
def patient_detail(patient_id):
    patient_data = get_patient_by_id(patient_id)

    if patient_data:
        return render_template("patient.html", patient = patient_data)
    else:
        return (f"No patient with ID {patient_id}", 404)

# run flask app and kafka consumer on localhost:8000
if __name__ == "__main__":
    print(f"Starting FLASK...")
    # socket_io.start_background_task(consume_kafka) # whitout this all works properly
    # print(f"Started KAFKA THREAD!")
    import threading
    threading.Thread(target=alert_consumer, daemon=True).start()
    threading.Thread(target=smart_data_consumer, daemon=True).start()
    socket_io.run(app, host="0.0.0.0", port=8000, allow_unsafe_werkzeug=True) # werkzeug only for debug