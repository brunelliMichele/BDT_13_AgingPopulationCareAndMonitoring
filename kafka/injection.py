import pandas as pd
import time
from datetime import datetime
from confluent_kafka import Producer

# Kafka config
config = {
    'bootstrap.servers': 'localhost:9092'
}

producer = Producer(config)

# load csv data
df = pd.read_csv("data/csv/smart_home_sensor/smart_home_dataset.csv")

# convertion of column "DATE" in timestamp and sort by time
df["DATE"] = df["DATE"].str.replace("_", ":") # modify time from 07_01_55 to 07:01:55
df["timestamp"] = pd.to_datetime(df["DATE"], format = "%Y-%m-%d %H:%M:%S")
df.sort_values("timestamp", inplace = True)

# set a variable for the starting time
start = df["timestamp"].iloc[0]

# error handling
def delivery_report(err, msg):
    if err is not None:
        print(f"Error raised: {err}")
    else:
        print(f"Sended: {msg.value().decode('utf-8')}")

# injection
for i in range(len(df)):
    row = df.iloc[i]
    msg = row.to_json()

    if i > 0:
        prev_ts = df["timestamp"].iloc[i-1] # previous time
        curr_ts = row["timestamp"] # current time
        delta = (curr_ts - prev_ts).total_seconds()
        time.sleep(max(0, delta)) # sleep for "delta" time avoiding negative
    
    producer.produce("smart_home_sensors", value = msg, callback = delivery_report) # send the data in the "smart_home_sensors" topic with kafka
    producer.poll(0)

producer.flush()