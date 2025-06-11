# config.py

# This module loads environment variables and provides configuration constants
# for database and Kafka connections used throughout the application.
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection configuration
DB_HOST = os.environ.get("DB_HOST", "db")
DB_PORT = int(os.environ.get("DB_PORT", 5432))
DB_NAME = os.environ.get("DB_NAME", "medicalData")
DB_USER = os.environ.get("DB_USER", "user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")

# Kafka message broker configuration
KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "kafka:9092")
SMART_TOPIC = os.environ.get("SMART_TOPIC", "smart_home_data")
ALERT_TOPIC = os.environ.get("ALERT_TOPIC", "alert_topic")
RISK_TOPIC = os.environ.get("RISK_TOPIC", "risk_alerts")
