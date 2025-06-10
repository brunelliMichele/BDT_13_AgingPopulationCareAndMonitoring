# === IMPORTS ===
import random
import time
import json
from datetime import datetime, timezone
import pytz
from confluent_kafka import Producer
from sqlalchemy import create_engine, text
import os
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === GLOBAL VARIABLES ===
KAFKA_CONFIG = {"bootstrap.servers": "kafka:9092"}
KAFKA_TOPIC_SMART = "smart_home_data"
KAFKA_TOPIC_ALERT = "alert_topic"
ROOMS = ["Kitchen", "Living Room", "Bathroom", "Bedroom", "Laundry Room"]

DB_HOST = os.environ.get("DB_HOST", "db")
DB_PORT = int(os.environ.get("DB_PORT", 5432))
DB_NAME = os.environ.get("DB_NAME", "medicalData")
DB_USER = os.environ.get("DB_USER", "user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")

# === FUNCTION ===

# db connection
def get_db_engine():
    db_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(db_url)

# get ids from db
def get_patients():
    for attempt in range(20):
        try:
            engine = get_db_engine()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT id, first, last FROM patients;"))
                patients = {str(row.id): f"{row.first} {row.last}" for row in result}
                if patients:
                    return patients
                else:
                    logging.info(f"Attempt {attempt+1}/20 - Waiting for patients to be inserted...")
        except Exception as e:
            logging.info(f"Attempt {attempt+1}/20 - Waiting for database... {e}")
        time.sleep(3)
    raise Exception("❌ Database not reachable or patients table is empty")

# data generation
def get_temperature(room):
    hour = datetime.now(timezone.utc).hour
    base_temp = {
        "Kitchen": 22,
        "Living Room": 21,
        "Bathroom": 24,
        "Bedroom": 21,
        "Laundry Room": 21
    }.get(room, 20)

    # lowers the temperature at night
    if hour < 6 or hour > 22:
        base_temp -= 2

    return round(random.normalvariate(base_temp, 1.2), 1)

def get_humidity(room):
    base_humidity = {
        "Bathroom": 60,
        "Kitchen": 60,
        "Living Room": 45,
        "Bedroom": 50,
        "Laundry Room": 55
    }.get(room, 50)

    variation = random.uniform(-5, 5)
    return round(base_humidity + variation, 1)

def get_status(device=None):
    hour = datetime.now(timezone.utc).hour

    if device in ["TV", "Lamp"] and 18 <= hour <= 23:
        return random.choices(["On", "Off"], weights=[0.6, 0.4])[0]
    elif device in ["Washer", "Dryer"] and 9 <= hour <= 18:
        return random.choices(["On", "Off"], weights=[0.4, 0.6])[0]
    elif device in ["Fridge"]:
        return "On"  # sempre acceso
    else:
        return random.choices(["On", "Off"], weights=[0.2, 0.8])[0]

def device_type(room):
    devices = {
        "Kitchen": ["Fridge", "Microwave", "Oven"],
        "Living Room": ["TV", "Lamp", "Fan"],
        "Bathroom": ["Heater", "Hair Dryer"],
        "Bedroom": ["Lamp", "Heater"],
        "Laundry Room": ["Washing Machine", "Dryer"]
    }
    return devices.get(room, [])

# alert functions
def check_temperature_alert(temp, room, user_id, patient_name):
    if temp > 28.0:
        return f"{patient_name} - HIGH temp in {room}: {temp}°C"
    elif temp < 16.0:
        return f"{patient_name} - LOW temp in {room}: {temp}°C"
    return None

def check_humidity_alert(humidity, room, user_id, patient_name):
    if humidity > 70.0:
        return f"{patient_name} - HIGH humidity in {room}: {humidity}%"
    elif humidity < 35.0:
        return f"{patient_name} - LOW humidity in {room}: {humidity}%"
    return None

def check_device_duration_alert(device, duration, room, user_id, patient_name, alerted_devices):
    if duration > 15:
        if not alerted_devices[user_id].get(device):
            alerted_devices[user_id][device] = True
            return f"{patient_name} - {device} running > 15min in {room}"
        else:
            if alerted_devices[user_id].get(device):
                alerted_devices[user_id][device] = False
    return None

# kafka error handler
def delivery_report(err, msg):
    if err is not None:
        logging.error(f"Delivery failed: {err}")
    else:
        logging.info(f"Message delivered to {msg.topic()} [{msg.partition()}]")

# save alert in alerts table on db
def save_alert_to_db(patient_id, alert_type, room, message, timestamp):
    engine = get_db_engine()
    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO alerts (patient_id, alert_type, room, message, timestamp) VALUES (:pid, :atype, :room, :msg, :ts)"),
            {"pid": patient_id, "atype": alert_type, "room": room, "msg": message, "ts": timestamp}
        )

# simulate real time data
def simulate_realtime():
    producer = Producer(KAFKA_CONFIG)
    people_map = get_patients()
    people = list(people_map.keys())
    alerted_devices = {pid: {} for pid in people}
    device_states = {pid: {} for pid in people}

    while True:
        timestamp = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=pytz.UTC)
        active_people = random.sample(people, k = int(len(people) * 0.7)) # 70% active people
        snapshot = {}
        alerts = []

        for pid in active_people:
            user_id = str(pid)
            patient_name = people_map[pid]
            person_data = {"rooms": {}}

            for room in ROOMS:
                appliances = device_type(room)
                temp = get_temperature(room)
                humidity = get_humidity(room)
                room_appliances = {}

                # Check alerts
                for fn in [check_temperature_alert, check_humidity_alert]:
                    alert = fn(temp if fn == check_temperature_alert else humidity, room, user_id, patient_name)
                    if alert:
                        alerts.append({
                            "message": alert,
                            "patient_id": str(pid)
                        })
                        save_alert_to_db(patient_id=pid, alert_type="temperature" if fn == check_temperature_alert else "humidity", room=room, message=alert, timestamp=timestamp)

                for device in appliances:
                    prev = device_states[pid].get(device, {"Status": "Off", "Duration": 0})
                    status = get_status()
                    duration = prev["Duration"] + 1 if prev["Status"] == "On" and status == "On" else (1 if status == "On" else 0)
                    device_states[pid][device] = {"Status": status, "Duration": duration}

                    alert = check_device_duration_alert(device, duration, room, user_id, patient_name, alerted_devices)
                    if alert:
                        alerts.append({
                            "message": alert,
                            "patient_id": str(pid)
                        })
                        save_alert_to_db(patient_id=pid, alert_type="duration", room=room, message=alert, timestamp=timestamp)

                    room_appliances[device] = {"Status": status, "Duration (min)": duration}

                person_data["rooms"][room] = {
                    "temperature": temp,
                    "humidity": humidity,
                    "appliances": room_appliances
                }
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            snapshot[user_id] = {
                "patient_id": user_id,
                "patient_name": patient_name,
                "timestamp": timestamp_str,
                "data": person_data
            }

        with open("house_data.json", "w") as f:
            json.dump(snapshot, f, indent=4)

        producer.produce(KAFKA_TOPIC_SMART, value=json.dumps(snapshot).encode(), callback=delivery_report)

        if alerts:
            max_alerts_per_cycle = 10
            alerts = alerts[:max_alerts_per_cycle]

            with open("alerts.log", "a") as f:
                for alert in alerts:
                    f.write(f"{timestamp} {alert}\n")
            if len(alerts) > max_alerts_per_cycle:
                logging.warning(f"Alert count capped at {max_alerts_per_cycle} (original: {len(alerts)})")
            logging.info(f"[{timestamp}] ALERTS TRIGGERED:\n" + "\n".join(a["message"] for a in alerts))
            producer.produce(KAFKA_TOPIC_ALERT, value=json.dumps(alerts).encode(), callback=delivery_report)
        else:
            logging.info(f"[{timestamp}] No alerts. System OK.")

        producer.flush()
        time.sleep(10)


# === MAIN ===
if __name__ == "__main__":
    simulate_realtime()