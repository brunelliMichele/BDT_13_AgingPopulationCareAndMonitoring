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

    with engine.begin() as conn:
        metadata = MetaData()
        vital_signs = Table("vital_signs", metadata, autoload_with=conn)
        for _, row in df_to_save.iterrows():
            stmt = insert(vital_signs).values(row.to_dict())
            stmt = stmt.on_conflict_do_nothing(index_elements=["patient_id", "date"])
            conn.execute(stmt)


if __name__ == "__main__":
    main()
