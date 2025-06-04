import json
import os
import pandas as pd
import psycopg2
from confluent_kafka import Producer
from sqlalchemy import create_engine, text
import time
import sys
sys.stdout.reconfigure(line_buffering=True)

# Kafka producer setup
producer = Producer({
    'bootstrap.servers': 'kafka:9092'
})

def delivery_report(err, msg):
    if err is not None:
        print(f"⚠️ Delivery failed for record {msg.key()}: {err}")
    else:
        print(f"✅ Record successfully produced to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

# Connect to PostgreSQL
DB_USER = os.environ.get("DB_USER", "user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")
DB_HOST = os.environ.get("DB_HOST", "db")
DB_NAME = os.environ.get("DB_NAME", "medicalData")

engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}")

def wait_for_table(engine, table_name):
    while True:
        try:
            with engine.connect() as conn:
                res = conn.execute(text(
                    "SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = :t"
                ), {"t": table_name})
                if res.fetchone():
                    print(f"✅ Table '{table_name}' is available.")
                    return
                else:
                    print(f"⏳ Waiting for table '{table_name}' to be created...")
        except Exception as e:
            print(f"⚠️ DB connection failed: {e}")
        time.sleep(5)

wait_for_table(engine, "vital_signs")


# # Fetch high-risk patients from recent data [FOR PRODUCTION]
# query = """
# SELECT patient_id, risk_level, date
# FROM vital_signs
# WHERE date > NOW() - interval '1 hour' AND risk_level > 60;
# """

# Fetch high-risk patients  [DEBUG]
query = """
SELECT 
    vs.patient_id, 
    vs.risk_level, 
    vs.date, 
    p.first,
    p.middle,
    p.last
FROM vital_signs vs
JOIN patients p ON vs.patient_id = p.id
WHERE risk_level > 40;
"""

while True:
    try:
        print("🔍 Checking for high-risk patients...")
        df = pd.read_sql(query, engine)
        print(f"📋 Retrieved {len(df)} high-risk records")

        for _, row in df.iterrows():
            print(f"📣 Sending alert for patient {row['patient_id']} with risk level {row['risk_level']}")
            alert = {
                "patient_id": str(row["patient_id"]),
                "first": row["first"],
                "middle": row["middle"],
                "last": row["last"],
                "risk_level": row["risk_level"],
                "category": (
                    "HIGH" if row["risk_level"] > 60 else
                    "MEDIUM" if row["risk_level"] > 30 else
                    "LOW"
                )
            }
            producer.produce("risk_alerts", value=json.dumps(alert).encode("utf-8"), callback=delivery_report)
            producer.flush()

    except Exception as e:
        print(f"⚠️ Error while generating alerts: {e}")

    time.sleep(60)