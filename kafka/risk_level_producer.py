import json
import os
import pandas as pd
import psycopg2
from confluent_kafka import Producer, Consumer
from sqlalchemy import create_engine, text
from datetime import datetime
import time
import sys
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

RISK_THRESHOLD = 60  # adjust as needed

# Kafka producer for sending risk alerts
producer = Producer({
    'bootstrap.servers': 'kafka:9092'
})
# kafka consumer to get vital signs data
consumer = Consumer({
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'risk_evaluator_debug_1',
    'auto.offset.reset': 'earliest'
})

consumer.subscribe(['vital_signs_stream'])

# checks delivery of kafka messages
def delivery_report(err, msg):
    if err is not None:
        logging.error(f"Delivery failed for record {msg.key()}: {err}")
    else:
        logging.info(f"Record successfully produced to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

# Connect to PostgreSQL
DB_USER = os.environ.get("DB_USER", "user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")
DB_HOST = os.environ.get("DB_HOST", "db")
DB_NAME = os.environ.get("DB_NAME", "medicalData")

engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}")

# prevent kafka consumer to start before tha database is ready
def wait_for_table(engine, table_name):
    while True:
        try:
            with engine.connect() as conn:
                res = conn.execute(text(
                    "SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = :t"
                ), {"t": table_name})
                if res.fetchone():
                    logging.info(f"Table '{table_name}' is available.")
                    return
                else:
                    logging.info(f"Waiting for table '{table_name}' to be created...")
        except Exception as e:
            logging.warning(f"DB connection failed: {e}")
        time.sleep(5)

wait_for_table(engine, "vital_signs")

# === MAIN CONSUMER LOOP ===
while True:
    # checks every second for new messages
    msg = consumer.poll(1.0)
    if msg is None:
        logging.info("No message received")
        continue
    if msg.error():
        logging.error(f"Consumer error: {msg.error()}")
        continue

    try:
        # extract patient infos and risk score
        # logging.info(f"🟢 Raw message: {msg.value()}") - debug
        data = json.loads(msg.value().decode("utf-8"))
        # logging.info(f"🟢 Parsed JSON: {data}") - debug
        patient_id = data.get("patient_id")
        observation_date = data.get("date")
        risk_level = data.get("risk_level", 0)

        logging.info(f"Received Kafka message: patient_id={patient_id}, date={observation_date}, risk_level={risk_level}")

        # Verify it's the latest info for that patient
        with engine.connect() as conn:
            res = conn.execute(text("""
                SELECT date FROM vital_signs
                WHERE patient_id = :pid
                ORDER BY date DESC
                LIMIT 1
            """), {"pid": patient_id})
            latest = res.scalar()

        logging.info(f"Latest date in DB for patient {patient_id}: {latest}")

        # only generate alert if the risk is above threshold
        obs_dt = datetime.fromisoformat(observation_date)
        if obs_dt == latest and risk_level > RISK_THRESHOLD:
            with engine.connect() as conn:
                res = conn.execute(
                    text("""SELECT first, middle, last FROM patients WHERE id = :pid"""),
                    {"pid": patient_id}
                ).mappings().first()
            if res:
                full_name = " ".join(filter(None, [res["first"], res["middle"], res["last"]]))
            else:
                logging.error("Name not found")

            # define risk levels
            category = (
                "HIGH" if risk_level > 60 else
                "MEDIUM" if risk_level > 30 else
                "LOW"
            )
            # compose alert message
            message = f"🚨 {full_name} - Risk level {risk_level} ({category})"
            alert = {
                "patient_id": str(patient_id),
                "patient_name": full_name,
                "risk_level": risk_level,
                "category": category,
                "message": message
            }
            logging.info(f"Producing alert: {json.dumps(alert, indent=2)}")
            # send alerts to the kafka topic
            producer.produce("risk_alerts", value=json.dumps(alert).encode("utf-8"), callback=delivery_report)
            producer.flush()

    except Exception as e:
        logging.error(f"Error while generating alerts: {e}")