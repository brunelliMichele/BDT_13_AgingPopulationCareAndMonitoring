from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dropout, Dense
from tensorflow.keras.callbacks import EarlyStopping
from sqlalchemy import create_engine, text, Table, MetaData
from sqlalchemy.dialects.postgresql import insert
from tensorflow.keras import Input
import joblib
import os
import sys
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
from kafka import KafkaProducer
import json
import uuid
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
import time
sys.path.append("/shared")
from process_patient_data import process_observations

# === PATHS ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

model_path = os.path.join(OUTPUT_DIR, "model.keras")
scaler_x_path = os.path.join(OUTPUT_DIR, "scaler_x.pkl")
scaler_y_path = os.path.join(OUTPUT_DIR, "scaler_y.pkl")

# === GLOBAL VARIABLES ===
DB_HOST = os.environ.get("DB_HOST", "db")
DB_PORT = int(os.environ.get("DB_PORT", 5432))
DB_NAME = os.environ.get("DB_NAME", "medicalData")
DB_USER = os.environ.get("DB_USER", "user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")

topic_name = "vital_signs_stream"

def ensure_topic_ready(topic, bootstrap_servers="kafka:9092", retries=10, delay=1):
    admin_client = KafkaAdminClient(bootstrap_servers=bootstrap_servers)
    try:
        admin_client.create_topics([NewTopic(name=topic, num_partitions=1, replication_factor=1)])
        logging.info(f"✅ Kafka topic '{topic}' created.")
    except TopicAlreadyExistsError:
        logging.info(f"ℹ️ Kafka topic '{topic}' already exists.")
    except Exception as e:
        logging.warning(f"⚠️ Could not create topic '{topic}': {e}")

    # Wait until the topic is available
    from kafka import KafkaConsumer
    for _ in range(retries):
        consumer = KafkaConsumer(bootstrap_servers=bootstrap_servers, group_id="topic_check")
        if topic in consumer.topics():
            logging.info(f"✅ Kafka topic '{topic}' is available.")
            return
        logging.info(f"⏳ Waiting for topic '{topic}' to become available...")
        time.sleep(delay)
    raise RuntimeError(f"❌ Kafka topic '{topic}' is not available after {retries} attempts.")

ensure_topic_ready(topic_name)

producer = KafkaProducer(
    bootstrap_servers=os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    linger_ms=10,
    batch_size=32768,
    retries=5
)

# === FUNCTIONS ===
def get_db_engine():
    db_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(db_url)

def create_sequences(x, y, window_size=6):
    x_seq, y_seq = [], []
    for i in range(len(x) - window_size):
        x_seq.append(x[i:i+window_size])
        y_seq.append(y[i+window_size])
    return np.array(x_seq), np.array(y_seq)

def main():
    engine = get_db_engine()
    df = process_observations(engine)

    if df.empty:
        return

    x_data = df[["HR", "RR", "body_temperature", "SpO2", "GSR"]].values
    y_data = df[["risk_level"]].values

    scaler_x = MinMaxScaler()
    scaler_y = MinMaxScaler()
    x_scaled = scaler_x.fit_transform(x_data)
    y_scaled = scaler_y.fit_transform(y_data)

    x_seq, y_seq = create_sequences(x_scaled, y_scaled, window_size=6)
    x_train, x_test, y_train, y_test = train_test_split(x_seq, y_seq, test_size=0.2, random_state=42)

    model = Sequential([
        Input(shape=(x_train.shape[1], x_train.shape[2])),
        LSTM(128, return_sequences=True),
        Dropout(0.3),
        LSTM(64),
        Dropout(0.3),
        Dense(1, activation="linear")
    ])
    model.compile(optimizer="adam", loss="mse", metrics=["mae"])
    model.fit(x_train, y_train, epochs=50, batch_size=128, validation_data=(x_test, y_test), callbacks=[EarlyStopping(patience=5, restore_best_weights=True)], verbose=1)
    logging.info("✅ Training completed. Saving model and scalers...")

    model.save(model_path)
    joblib.dump(scaler_x, scaler_x_path)
    joblib.dump(scaler_y, scaler_y_path)

    df_to_save = df[["patient_id", "date", "HR", "RR", "body_temperature", "SpO2", "GSR", "risk_level"]]
    df_to_save.columns = [col.lower() if col not in ("patient_id", "date", "risk_level") else col for col in df_to_save.columns]

    logging.info(f"📊 Numero righe da salvare: {len(df_to_save)}")
    logging.info(f"📊 Esempio dati:\n{df_to_save.head()}")

    with engine.begin() as conn:
        metadata = MetaData()
        vital_signs = Table("vital_signs", metadata, autoload_with=conn)
        for _, row in df_to_save.iterrows():
            logging.info(f"Tentativo di inserimento per: {row.to_dict()}")
            stmt = insert(vital_signs).values(row.to_dict())
            stmt = stmt.on_conflict_do_nothing(index_elements=["patient_id", "date"])
            result = conn.execute(stmt)
            if result.rowcount > 0:
                try:
                    record = row.to_dict()
                    if isinstance(record.get("patient_id"), uuid.UUID):
                        record["patient_id"] = str(record["patient_id"])
                    if isinstance(record.get("date"), pd.Timestamp):
                        record["date"] = record["date"].isoformat()
                    producer.send("vital_signs_stream", value=record)
                    logging.info(f"✅ Sent to vital_signs_stream: {record}")
                except Exception as e:
                    logging.error(f"❌ Kafka produce failed: {e}")
            else:
                logging.info(f"⏩ Dato già presente, non reinserito: {row['patient_id']} - {row['date']}")

    producer.flush()


if __name__ == "__main__":
    main()
