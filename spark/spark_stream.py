from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import *

# builder for the spark session
spark = SparkSession.builder \
    .appName("BDT_13_AgingPopulationCareAndMonitoring") \
    .getOrCreate()

# read from kafka topic
df = spark.readStrem \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "smart_home_sensors") \
    .option("startingOffsets", "earliest") \
    .load()

# data's scheme
scheme = StructType().add("Activity", StringType()).add("bed", IntegerType())

# JSON parsing
json_df = df.selectExpr("CAST(value as STRING)") \
    .select(from_json(col("value"), scheme).alias("data")) \
    .select("data.*")

# console output for testing
query = json_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

query.awaitTermination()