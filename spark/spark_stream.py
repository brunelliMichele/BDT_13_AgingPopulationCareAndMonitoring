from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType, IntegerType
from confluent_kafka import Producer
import json
import socket
import time

# wait for Kafka to be available
def wait_for_kafka(host = "kafka", port = 9092, timeout = 60):
    start_time = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout = 2):
                print("✅ Kafka is ready")
                return
        except OSError:
            if time.time() - start_time > timeout:
                raise TimeoutError("❌ Kafka is not ready after 60 seconds")
            print("⏳ Waiting for Kafka...")
            time.sleep(2)

# builder for the spark session
wait_for_kafka()
spark = SparkSession.builder \
    .appName("BDT_13_AgingPopulationCareAndMonitoring") \
    .getOrCreate()

# read from kafka topic smart_home_data
df_smart_home = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "smart_home_data") \
    .option("startingOffsets", "earliest") \
    .load()

# read from kafka topic alerts
df_alerts = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "alerts") \
    .option("startingOffsets", "earliest") \
    .load()

# data's scheme
scheme = StructType().add("Activity", StringType()).add("bed", IntegerType())

# JSON parsing for smart_home_data
json_smart_home_df = df_smart_home.selectExpr("CAST(value as STRING)") \
    .select(from_json(col("value"), scheme).alias("data")) \
    .select("data.*")

# JSON parsing for alerts
json_alerts_df = df_alerts.selectExpr("CAST(value as STRING)") \
    .select(from_json(col("value"), scheme).alias("data")) \
    .select("data.*")

producer = Producer({"bootstrap.servers": "kafka:9092"})

def forward_to_smart_home_data(batch_df, batch_id):
    print(f"📦 Batch recived for smart_home_data: {batch_id}, record number: {batch_df.count()}")
    records = batch_df.collect()
    for row in records:
        data = {"Activity": row["Activity"], "bed": row["bed"]}
        print(f"🔁 Forward message to smart_home_data topic: {data}")
        producer.produce("smart_home_data", key = "data", value = json.dumps(data))
        producer.flush()

def forward_to_alerts(batch_df, batch_id):
    print(f"📦 Batch recived for alerts: {batch_id}, record number: {batch_df.count()}")
    records = batch_df.collect()
    for row in records:
        data = {"Activity": row["Activity"], "bed": row["bed"]}
        print(f"🔁 Forward message to alerts topic: {data}")
        producer.produce("alerts", key = "alert", value = json.dumps(data))
        producer.flush()

query_smart = json_smart_home_df.writeStream \
    .foreachBatch(forward_to_smart_home_data) \
    .outputMode("append") \
    .start()

query_alerts = json_alerts_df.writeStream \
    .foreachBatch(forward_to_alerts) \
    .outputMode("append") \
    .start()

query_smart.awaitTermination()
query_alerts.awaitTermination()