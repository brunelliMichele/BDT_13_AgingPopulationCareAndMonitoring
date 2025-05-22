# sockets.py
from kafka import KafkaConsumer
import json
from threading import Thread
import logging
from flask_socketio import SocketIO, rooms
from config import KAFKA_BROKER, SMART_TOPIC, ALERT_TOPIC
from app import app

logging.basicConfig(level=logging.INFO)

def register_sockets(socket_io: SocketIO):
    @socket_io.on("connect")
    def on_connect():
        logging.info("✅ Client connected via WebSocket")

    def smart_data_consumer():
        with app.app_context():
            logging.info("📡 Starting smart_data_consumer thread...")
            try:
                consumer = KafkaConsumer(
                    SMART_TOPIC,
                    bootstrap_servers=KAFKA_BROKER,
                    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                    group_id="smart_data_group"
                )

                for message in consumer:
                    logging.info("🏠 Smart home data received.")
                    logging.info("🔍 Emitting smart_data_message...")
                    socket_io.emit("smart_data_message", message.value, to=None, namespace="/")

            except Exception as e:
                logging.error(f"❌ smart_data_consumer error: {e}")

    def alert_consumer():
        with app.app_context():
            logging.info("📡 Starting alert_consumer thread...")
            try:
                consumer = KafkaConsumer(
                    ALERT_TOPIC,
                    bootstrap_servers=KAFKA_BROKER,
                    value_deserializer=lambda a: json.loads(a.decode("utf-8")),
                    group_id="alert_group"
                )

                for message in consumer:
                    logging.info("⚠️ Alert received and sent.")
                    logging.info("🔍 Emitting alert...")
                    socket_io.emit("new_alert_message", message.value, to=None, namespace="/")

            except Exception as e:
                logging.error(f"❌ alert_consumer error: {e}")

    # Avvio thread
    Thread(target=smart_data_consumer, name="SmartDataConsumer", daemon=True).start()
    Thread(target=alert_consumer, name="AlertConsumer", daemon=True).start()
    