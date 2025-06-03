# sockets.py
from confluent_kafka import Consumer
import json
from threading import Thread
import logging
from flask_socketio import SocketIO, rooms
from config import KAFKA_BROKER, SMART_TOPIC, ALERT_TOPIC, RISK_TOPIC
from app import app
import time

logging.basicConfig(level=logging.INFO)

def register_sockets(socket_io: SocketIO):
    @socket_io.on("connect")
    def on_connect():
        logging.info("✅ Client connected via WebSocket")

    def smart_data_consumer():
        with app.app_context():
            logging.info("📡 Starting smart_data_consumer thread...")
            for _ in range(5):        
                try:
                    consumer = Consumer({
                        'bootstrap.servers': KAFKA_BROKER,
                        'group.id': 'smart_data_group',
                        'auto.offset.reset': 'earliest'
                    })
                    consumer.subscribe([SMART_TOPIC])
                    print("KafkaConsumer initialized for 'smart_home_data'")
                    break
                except Exception as e:
                    logging.warning(f"🔁 Retry smart_data_consumer: {e}")
                    time.sleep(5)
            else:
                logging.error("❌ smart_data_consumer failed to connect")
                return

            try:
                while True:
                    msg = consumer.poll(1.0)
                    if msg is None:
                        continue
                    if msg.error():
                        logging.error(f"Consumer error: {msg.error()}")
                        continue
                    logging.info("🏠 Smart home data received.")
                    logging.info("🔍 Emitting smart_data_message...")
                    socket_io.emit("smart_data_message", json.loads(msg.value().decode("utf-8")), to=None, namespace="/")
            
            except Exception as e:
                logging.error(f"❌ smart_data_consumer error: {e}")

    def alert_consumer():
        with app.app_context():
            logging.info("📡 Starting alert_consumer thread...")
            for _ in range(5):
                try:
                    consumer = Consumer({
                        'bootstrap.servers': KAFKA_BROKER,
                        'group.id': 'alert_group',
                        'auto.offset.reset': 'earliest'
                    })
                    consumer.subscribe([ALERT_TOPIC])
                    print("Kafka Consumer initialized for 'alert_topic'")
                except Exception as e:
                    logging.warning(f"🔁 Retry alert_consumer: {e}")
                    time.sleep(5)
                else:
                    logging.error("❌ alert_consumer failed to connect")

                try:
                    while True:
                        msg = consumer.poll(1.0)
                        if msg is None:
                            continue
                        if msg.error():
                            logging.error(f"Consumer error: {msg.error()}")
                            continue
                        logging.info("⚠️ Alert received.")
                        logging.info("🔍 Emitting alert...")
                        socket_io.emit("new_alert_message", json.loads(msg.value().decode("utf-8")), to=None, namespace="/")

                except Exception as e:
                    logging.error(f"❌ alert_consumer error: {e}")

    def risk_alert_consumer():
        with app.app_context():
            logging.info("📡 Starting risk_alert_consumer thread...")
            for _ in range(5):
                try:
                    consumer = Consumer({
                        'bootstrap.servers': KAFKA_BROKER,
                        'group.id': 'risk_alert_group',
                        'auto.offset.reset': 'earliest'
                    })
                    consumer.subscribe([RISK_TOPIC])
                    print("KafkaConsumer initialized for 'risk_alerts'")
                    break
                except Exception as e:
                    logging.warning(f"🔁 Retry risk_alert_consumer: {e}")
                    time.sleep(5)
            else:
                logging.error("❌ risk_alert_consumer failed to connect")
                return

            try:
                while True:
                    msg = consumer.poll(1.0)
                    if msg is None:
                        continue
                    if msg.error():
                        logging.error(f"Consumer error: {msg.error()}")
                        continue
                    logging.info("🚨 Risk alert received.")
                    logging.info("🔍 Emitting risk_alert_message...")
                    socket_io.emit("risk_alert_message", json.loads(msg.value().decode("utf-8")), to=None, namespace="/")
            except Exception as e:
                logging.error(f"❌ risk_alert_consumer error: {e}")

    # Avvio thread
    Thread(target=smart_data_consumer, name="SmartDataConsumer", daemon=True).start()
    Thread(target=alert_consumer, name="AlertConsumer", daemon=True).start()
    Thread(target=risk_alert_consumer, name="RiskAlertConsumer", daemon=True).start()