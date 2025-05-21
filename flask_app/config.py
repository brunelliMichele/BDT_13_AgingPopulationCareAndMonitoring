# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection config
DB_HOST = os.environ.get("DB_HOST", "db")
DB_PORT = int(os.environ.get("DB_PORT", 5432))
DB_NAME = os.environ.get("DB_NAME", "medicalData")
DB_USER = os.environ.get("DB_USER", "user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")

# KAFKA config
KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "kafka:29092")
SMART_TOPIC = os.environ.get("SMART_TOPIC", "smart_home_data")
ALERT_TOPIC = os.environ.get("ALERT_TOPIC", "alert_topic")

