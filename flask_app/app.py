from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from kafka import KafkaConsumer
import psycopg2
import os
import json

# create flask app and initialize webSocket
app = Flask(
    __name__,
    static_folder = "static",
    template_folder = "templates"
    )

socket_io = SocketIO(app, cors_allowed_origins = "*")

""" # Kafka Config
kafka_config = {
    "bootstrap.servers": "kafka:9092", # kafka container name
    "group.id": "smart_home", # consumer group name
    "auto.offset.reset": "earliest", # with no offset, start from the beginning
} 

# Kafka consumer with error handling
def consume_kafka():
    try:
        consumer = Consumer(kafka_config)
        print(f"Started kafka consumer") # log
        consumer.subscribe(["smart_home_data"])
        print(f"Kafka subsribed on topic 'smart_home_data'") #log

        while True:
            msg = consumer.poll(1.0)
            print(f"Polling...") # log
            if msg is None:
                print(f"No message recived") # log
                continue
            if msg.error():
                print(f"[KAFKA] - Error: {msg.error()}") # log
                continue
            data = msg.value().decode("utf-8")
            print(f"[MESSAGE DIMENSION] - {len(data)} bytes") # log
            print(f"📤 Emitting to socket: {data[:80]}...")  # log
            socket_io.emit('kafka_message', {'data': data})
            # socket_io.emit('kafka_message', {'data': "test"})
            print(f"[SocketIO] - Emit: {data[:80]}...") # log
        
        consumer.close()
    except Exception as e:
        import traceback
        print("❌ EXCEPTION in Kafka thread:")
        traceback.print_exc() """

def kafka_consumer():
    consumer = KafkaConsumer(
        'smart_home_data',
        bootstrap_servers='kafka:9092',
        value_deserializer = lambda m: json.loads(m.decode('utf-8'))
    )

    for message in consumer:
        socket_io.emit('kafka_message', message.value)

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
    cur.execute("SELECT id, first, middle, last, city, birthdate FROM patients")
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
            "url": f"/patient/{row[0]}"
        })
    cur.close()
    conn.close()
    return patients

# get all cities from postgres
def get_all_cities():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT city FROM patients WHERE city IS NOT NULL ORDER BY city;")
    rows = cur.fetchall()
    cities = [row[0] for row in rows]

    cur.close()
    conn.close()
    return cities

# Define city data
CITY_DATA = {
    "New York": [40.7128, -74.0060],
    "London": [51.5074, -0.1278],
    "Tokyo": [35.6762, 139.6503],
    "Paris": [48.8566, 2.3522],
    "Sydney": [-33.8688, 151.2093]
}


# set route for main page
@app.route("/")
def index():
    #cities = get_all_cities()
    cities = {
        "New York": [40.7128, -74.0060],
        "London": [51.5074, -0.1278],
        "Tokyo": [35.6762, 139.6503],
        "Paris": [48.8566, 2.3522],
        "Sydney": [-33.8688, 151.2093]
    }
    patients = get_all_patients()
    return render_template("index.html", patients=patients,cities=cities.keys(), city_data=cities)

# API route that returns JSON data
@app.route("/api/city-data")
def city_data():
    return jsonify(CITY_DATA)

# set route for patient detail page
@app.route("/patient/<string:patient_id>")
def patient_detail(patient_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, birthdate, deathdate, gender, birthplace, address, city, county, first, middle, last FROM patients WHERE id = %s", (patient_id,))
    patient = cur.fetchone()

    cur.close()
    conn.close()

    if patient:
        patient_data = {
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
        return render_template("patient.html", patient = patient_data)
    else:
        return f"No patient with ID {patient_id}", 404

# run flask app and kafka consumer on localhost:8000
if __name__ == "__main__":
    print(f"Starting FLASK...")
    # socket_io.start_background_task(consume_kafka) # whitout this all works properly
    # print(f"Started KAFKA THREAD!")
    import threading
    threading.Thread(target=kafka_consumer, daemon=True).start()
    socket_io.run(app, host="0.0.0.0", port=8000, allow_unsafe_werkzeug=True) # werkzeug only for debug