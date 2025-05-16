import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO
from confluent_kafka import Consumer
import psycopg2
import os

# create flask app and initialize webSocket
app = Flask(
    __name__,
    static_folder = "static",
    template_folder = "templates"
    )
socket_io = SocketIO(app, cors_allowed_origins = "*", async_mode="eventlet")

# Kafka Config
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
        traceback.print_exc()

# set postgres connection
def get_db_connection():
    return psycopg2.connect(
        host = os.environ.get("DB_HOST", "db"),
        port = 5432,
        database = os.environ.get("DB_NAME", "medicalData"),
        user = os.environ.get("DB_USER", "user"),
        password = os.environ.get("DB_PASSWORD", "password")
    )

# set primary route
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/patient/<string:patient_id>")
def patient_detail(patient_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, birthdate, deathdate, gender, birthplace, address, city, county FROM patients WHERE id = %s", (patient_id,))
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
            "county": patient[7]
        }
        return render_template("patient.html", patient = patient_data)
    else:
        return f"No patient with ID {patient_id}", 404

# run flask app and kafka consumer on localhost:8000
if __name__ == "__main__":
    print(f"Starting FLASK...")
    # socket_io.start_background_task(consume_kafka) # whitout this all works properly
    # print(f"Started KAFKA THREAD!")
    socket_io.run(app, host="0.0.0.0", port=8000)