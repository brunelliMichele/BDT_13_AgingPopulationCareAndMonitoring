import random
import time
import json
from datetime import datetime
from Alert_functions import *
import pytz
from confluent_kafka import Producer

def device_type(room):
    devices_by_room = {
        "Kitchen": ["Oven", "Refrigerator", "Microwave", "Dishwasher"],
        "Living Room": ["Television", "Air Conditioner", "Computer"],
        "Bathroom": ["Hair Dryer", "Heater"],
        "Bedroom": ["Fan", "Heater", "Television"],
        "Laundry Room": ["Washing Machine", "Dryer"],
    }
    return devices_by_room.get(room, [])

def get_temperature(min_temp=10.0, max_temp=30.0, anomaly_chance=0.001):
    if random.random() < anomaly_chance:
        if random.choice(["low", "high"]) == "low":
            return round(random.uniform(5.0, min_temp - 0.1), 1)
        else:
            return round(random.uniform(max_temp + 0.1, 35.0), 1)
    else:
        return round(random.uniform(min_temp, max_temp), 1)

def get_humidity(min_humidity=40.0, max_humidity=60.0, anomaly_chance=0.001):
    if random.random() < anomaly_chance:
        if random.choice(["low", "high"]) == "low":
            return round(random.uniform(20.0, min_humidity - 0.1), 1)
        else:
            return round(random.uniform(max_humidity + 0.1, 80.0), 1)
    else:
        return round(random.uniform(min_humidity, max_humidity), 1)

def get_status():
    return random.choice(["On", "Off"])

# Patients
people = list(range(1, 21))

# error handling for kafka
def delivery_report(err, msg):
    if err is not None:
        print(f"Error raised: {err}")
    else:
        print(f"Message sended to {msg.topic()}")

def simulate_realtime():

    # configuration of Kafka Server
    config = {
        "bootstrap.servers": "kafka:9092"
    }

    # open connection with Kafka Server
    producer = Producer(config)

    rooms = ["Kitchen", "Living Room", "Bathroom", "Bedroom", "Laundry Room"]
    person_device_states = {patient_id: {} for patient_id in people}

    while True:
        current_time = datetime.utcnow().replace(microsecond=0, tzinfo=pytz.UTC)
        timestamp_str = current_time.strftime("%Y-%m-%d %H:%M:%S")

        snapshot = {}
        alerts = []

        for patient_id in people:
            user_id = f"user_{str(patient_id).zfill(3)}"
            person_data = {
                "rooms": {}
            }

            for room in rooms:
                appliances = device_type(room)
                temperature = get_temperature()
                humidity = get_humidity()
                appliances_data = {}

                # Alerts
                alert_temp = check_temperature_alert(temperature, room, user_id)
                if alert_temp:
                    alerts.append(alert_temp)

                alert_humidity = check_humidity_alert(humidity, room, user_id)
                if alert_humidity:
                    alerts.append(alert_humidity)

                for appliance in appliances:
                    if appliance not in person_device_states[patient_id]:
                        person_device_states[patient_id][appliance] = {"Status": "Off", "Duration": 0}

                    prev = person_device_states[patient_id][appliance]
                    status = get_status()

                    if status == "On" and prev["Status"] == "On":
                        duration = prev["Duration"] + 1
                    elif status == "On":
                        duration = 1
                    else:
                        duration = 0

                    person_device_states[patient_id][appliance] = {
                        "Status": status,
                        "Duration": duration
                    }

                    alert_duration = check_device_duration_alert(appliance, duration, room, user_id)
                    if alert_duration:
                        alerts.append(alert_duration)

                    appliances_data[appliance] = {
                        "Status": status,
                        "Duration (min)": duration
                    }

                person_data["rooms"][room] = {
                    "temperature": temperature,
                    "humidity": humidity,
                    "appliances": appliances_data
                }

            snapshot[user_id] = {
                timestamp_str: person_data
            }

        with open("house_data.json", "w") as json_file:
            json.dump(snapshot, json_file, indent=4)

        producer.produce("smart_home_data", value = json.dumps(snapshot).encode('utf-8'), callback = delivery_report)
        producer.flush()
        print(f"[KAFKA] - Send message {json.dumps(snapshot)[:100]} on topic 'smart_home_data")

        if alerts:
            with open("alerts.log", "a") as alert_file:
                for alert in alerts:
                    alert_file.write(f"{timestamp_str} {alert}\n")
            print(f"[{current_time}] ALERTS TRIGGERED:\n" + "\n".join(alerts))
            producer.produce("alert_topic", value = json.dumps(alert).encode("utf-8"), callback = delivery_report)
        else:
            print(f"[{current_time}] No alerts. System operating normally.")

        time.sleep(10)

simulate_realtime()

