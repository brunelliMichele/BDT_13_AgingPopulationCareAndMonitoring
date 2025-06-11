# sockets.py

# This script sets up WebSocket event handlers and background Kafka consumer threads 
# for real-time streaming of smart home data, general alerts, and risk alerts to the frontend.

from confluent_kafka import Consumer
import json
from threading import Thread
import logging
from flask_socketio import SocketIO, rooms
from config import KAFKA_BROKER, SMART_TOPIC, ALERT_TOPIC, RISK_TOPIC
from app import app
import time
logging.basicConfig(level=logging.INFO)

# Register WebSocket event handlers and start Kafka consumers
def register_sockets(socket_io: SocketIO):
    # Event triggered when a WebSocket client connects
    @socket_io.on("connect")
    def on_connect():
        logging.debug("✅ Client connected via WebSocket")

    # Consumer thread for processing smart home data from Kafka
    def smart_data_consumer():
        with app.app_context():
            logging.debug("📡 Starting smart_data_consumer thread...")
            # Retry Kafka connection up to 5 times with delay
            for _ in range(5):        
                try:
                    consumer = Consumer({
                        'bootstrap.servers': KAFKA_BROKER,
                        'group.id': 'smart_data_group',
                        'auto.offset.reset': 'earliest'
                    })
                    consumer.subscribe([SMART_TOPIC])
                    logging.info("KafkaConsumer initialized for 'smart_home_data'")
                    break
                except Exception as e:
                    logging.warning(f"🔁 Retry smart_data_consumer: {e}")
                    time.sleep(5)
            else:
                logging.error("❌ smart_data_consumer failed to connect")
                return

            try:
                while True:
                    # Poll Kafka for new messages and handle smart home data
                    msg = consumer.poll(1.0)
                    if msg is None:
                        continue
                    if msg.error():
                        logging.error(f"Consumer error: {msg.error()}")
                        continue

                    logging.info("🏠 Smart home data received.")

                    try:
                        raw = msg.value().decode("utf-8")
                        data = json.loads(raw)
                        logging.debug(f"📦 Raw smart data: {json.dumps(data, indent=2)}")

                        # Validate message format before emitting to WebSocket
                        if isinstance(data, dict) and any(
                            isinstance(v, dict) and "patient_id" in v for v in data.values()
                        ):
                            logging.info("🔍 Emitting smart_data_message...")
                            socket_io.emit("smart_data_message", data, to=None, namespace="/")
                        else:
                            logging.warning("⚠️ Invalid message structure for smart_data_message.")
                    
                    except Exception as parse_err:
                        logging.error(f"❌ Error parsing or emitting Kafka message: {parse_err}")
            
            except Exception as e:
                logging.error(f"❌ smart_data_consumer error: {e}")

    # Consumer thread for processing general alerts from Kafka
    def alert_consumer():
        with app.app_context():
            logging.debug("📡 Starting alert_consumer thread...")
            # Retry Kafka connection up to 5 times with delay
            for _ in range(5):
                try:
                    consumer = Consumer({
                        'bootstrap.servers': KAFKA_BROKER,
                        'group.id': 'alert_group',
                        'auto.offset.reset': 'earliest'
                    })
                    consumer.subscribe([ALERT_TOPIC])
                    logging.debug("Kafka Consumer initialized for 'alert_topic'")
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

                        try:
                            raw = msg.value().decode("utf-8")
                            data = json.loads(raw)


                            # Validate alert message and emit to WebSocket
                            is_valid = (
                                isinstance(data, list) and all(isinstance(x, dict) and "message" in x and "patient_id" in x for x in data)
                            ) or (
                                isinstance(data, dict) and "message" in data and "patient_id" in data
                            )

                            if is_valid:
                                logging.info("🔍 Emitting new_alert_message...")
                                socket_io.emit("new_alert_message", data, to=None, namespace="/")
                            else:
                                logging.warning("⚠️ Invalid or malformed alert message.")

                        except Exception as parse_err:
                            logging.error(f"❌ Error parsing or emitting alert: {parse_err}")
                
                except Exception as e:
                    logging.error(f"❌ alert_consumer error: {e}")

    # Consumer thread for processing risk alerts from Kafka
    def risk_level_consumer():
        with app.app_context():
            logging.debug("📡 Starting risk_alert_consumer thread...")
            # Retry Kafka connection up to 5 times with delay
            for _ in range(5):
                try:
                    consumer = Consumer({
                        'bootstrap.servers': KAFKA_BROKER,
                        'group.id': 'risk_alert_group',
                        'auto.offset.reset': 'earliest'
                    })
                    consumer.subscribe([RISK_TOPIC])
                    logging.debug("KafkaConsumer initialized for 'risk_alerts'")
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
                    # Decode and enrich alert data, then emit via WebSocket
                    logging.info("🔍 Emitting risk_alert_message...")
                    alert_data = json.loads(msg.value().decode("utf-8"))

                    if isinstance(alert_data, dict):
                        patient = alert_data.get("patient_name", "Unknown")
                        risk = alert_data.get("risk_level", alert_data.get("message", "unspecified risk"))

                        if "message" not in alert_data or not alert_data["message"]:
                            alert_data["message"] = f"🚨 {patient} - Risk detected: {risk}"

                    logging.info(f"🚨 Emitting risk alert: {alert_data}")
                    socket_io.emit("risk_alert_message", alert_data, to=None, namespace="/")
                    
            except Exception as e:
                logging.error(f"❌ risk_alert_consumer error: {e}")

    # Start all consumer threads as daemon background tasks
    Thread(target=smart_data_consumer, name="SmartDataConsumer", daemon=True).start()
    Thread(target=alert_consumer, name="AlertConsumer", daemon=True).start()
    Thread(target=risk_level_consumer, name="RiskLevelConsumer", daemon=True).start()