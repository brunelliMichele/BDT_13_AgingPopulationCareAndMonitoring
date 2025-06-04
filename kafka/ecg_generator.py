import math
import time
import random
import json
import psycopg2
from datetime import datetime, timezone
from confluent_kafka import Producer
import os

KAFKA_CONFIG = {'bootstrap.servers': 'kafka:9092'}
KAFKA_TOPIC = 'ecg_data'

def simulate_ecg_wave(t, bpm=75):
    frequency = bpm/60
    noise = random.normalvariate(0, 0.02)
    return round(math.sin(2 * math.pi * frequency * t) + noise, 3)

def get_db_connection():
    return psycopg2.connect(
        host = os.environ.get("DB_HOST", "db"),
        port = 5432,
        database = os.environ.get("DB_NAME", "medicalData"),
        user = os.environ.get("DB_USER", "user"),
        password = os.environ.get("DB_PASSWORD", "password")
    )

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
people_map = get_patients()
PATIENT_IDS = list(people_map.keys())

def delivery_report(err, msg):
    if err is not None:
        print(f'❌ Message delivery failed: {err}')
    else:
        print(f'✅ Message delivery succeeded: {msg.topic()} [{msg.partition()}]')
def main():
    producer = Producer(KAFKA_CONFIG)
    start_time = time.time()

    while True:
        now = datetime.now(timezone.utc)
        t = time.time() - start_time

        for pid in PATIENT_IDS:
            value = simulate_ecg_wave(t)
            payload = {
                'patient_id': pid,
                'timestamp': now.isoformat(),
                'lead': 'Lead I',
                'voltage': value,
            }
            producer.produce(KAFKA_TOPIC, value=json.dumps(payload), callback=delivery_report)
        producer.flush()
        time.sleep(0.1)
if __name__ == '__main__':
    main()
