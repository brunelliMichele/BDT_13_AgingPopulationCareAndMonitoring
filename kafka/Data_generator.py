# === IMPORTS ===
import random
import time
import json
from datetime import datetime, timezone
import pytz
from confluent_kafka import Producer
import psycopg2
import os

# === CONFIG ===
KAFKA_CONFIG = {"bootstrap.servers": "kafka:9092"}
KAFKA_TOPIC_SMART = "smart_home_data"
KAFKA_TOPIC_ALERT = "alert_topic"
ROOMS = ["Kitchen", "Living Room", "Bathroom", "Bedroom", "Laundry Room"]

# === FUNCTION ===

# db connection
def get_db_connection():
    return psycopg2.connect(
        host = os.environ.get("DB_HOST", "db"),
        port = 5432,
        database = os.environ.get("DB_NAME", "medicalData"),
        user = os.environ.get("DB_USER", "user"),
        password = os.environ.get("DB_PASSWORD", "password")
    )

# get ids from db
def get_patients():
    for attempt in range(20):  # retry 20 times
        try:
            conn = get_db_connection()
            break
        except psycopg2.OperationalError as e:
            print(f"⏳ Attempt {attempt+1}/20 - Waiting for database... {e}")
            time.sleep(3)
    else:
        raise Exception("❌ Database not reachable")

    cur = conn.cursor()
    cur.execute("SELECT id, first, last FROM patients;")
    patients = {str(row[0]): f"{row[1]} {row[2]}" for row in cur.fetchall()}
    cur.close()
    conn.close()
    return patients

# data generation
def get_temperature(room):
    hour = datetime.now(timezone.utc).hour
    base_temp = {
        "Kitchen": 22,
        "Living Room": 21,
        "Bathroom": 24,
        "Bedroom": 19,
        "Laundry Room": 18
    }.get(room, 20)

    # lowers the temperature at night
    if hour < 6 or hour > 22:
        base_temp -= 2

    return round(random.normalvariate(base_temp, 1.2), 1)

def get_humidity(room):
    base_humidity = {
        "Bathroom": 70,
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
        print(f"❌ Delivery failed: {err}")
    else:
        print(f"✅ Message delivered to {msg.topic()} [{msg.partition()}]")

# save alert in alerts table on db
def save_alert_to_db(patient_id, alert_type, room, message, timestamp):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO alerts (patient_id, alert_type, room, message, timestamp) VALUES (%s, %s, %s, %s, %s)", (patient_id, alert_type, room, message, timestamp))
    conn.commit()
    cur.close()
    conn.close()

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
                        alerts.append(alert)
                        save_alert_to_db(patient_id=pid, alert_type="temperature" if fn == check_temperature_alert else "humidity", room=room, message=alert, timestamp=timestamp)

                for device in appliances:
                    prev = device_states[pid].get(device, {"Status": "Off", "Duration": 0})
                    status = get_status()
                    duration = prev["Duration"] + 1 if prev["Status"] == "On" and status == "On" else (1 if status == "On" else 0)
                    device_states[pid][device] = {"Status": status, "Duration": duration}

                    alert = check_device_duration_alert(device, duration, room, user_id, patient_name, alerted_devices)
                    if alert:
                        alerts.append(alert)
                        save_alert_to_db(patient_id=pid, alert_type="duration", room=room, message=alert, timestamp=timestamp)

                    room_appliances[device] = {"Status": status, "Duration (min)": duration}

                person_data["rooms"][room] = {
                    "temperature": temp,
                    "humidity": humidity,
                    "appliances": room_appliances
                }
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            snapshot[user_id] = {timestamp_str: person_data}

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
                print(f"⚠️ Alert count capped at {max_alerts_per_cycle} (original: {len(alerts)})")
            print(f"[{timestamp}] ALERTS TRIGGERED:\n" + "\n".join(alerts))
            producer.produce(KAFKA_TOPIC_ALERT, value=json.dumps(alerts).encode(), callback=delivery_report)
        else:
            print(f"[{timestamp}] No alerts. System OK.")

        producer.flush()
        time.sleep(10)


# === MAIN ===
if __name__ == "__main__":
    simulate_realtime()