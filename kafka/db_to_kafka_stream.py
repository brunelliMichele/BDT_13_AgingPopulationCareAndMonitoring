from confluent_kafka import Producer
import pandas as pd
import json
import time

TOPIC = "csv_sensor_stream"  # or use 'smart_home_sensor'

conf = {
    'bootstrap.servers': 'kafka:9092'  # Same as your working data_generator.py
}

producer = Producer(conf)

def acked(err, msg):
    if err is not None:
        print("❌ Delivery failed:", err)
    else:
        print(f"✅ Delivered to {msg.topic()} [{msg.partition()}]")

# Load CSV (you can change to any data file)
df = pd.read_csv("/app/data/observations.csv")
df = df.sort_values(by="DATE")

# Stream each row to Kafka
for _, row in df.iterrows():
    msg = json.dumps(row.to_dict(), default=str)
    producer.produce(TOPIC, value=msg, callback=acked)
    producer.poll(0)  # trigger delivery report
    time.sleep(1)

producer.flush()


