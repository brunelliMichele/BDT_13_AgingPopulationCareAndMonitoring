import pandas as pd
import numpy as np
import tensorflow as tf
import joblib
import sys
import os
from sqlalchemy import create_engine, text

# === GLOBAL VARIABLES ===
DB_HOST = os.environ.get("DB_HOST", "db")
DB_PORT = int(os.environ.get("DB_PORT", 5432))
DB_NAME = os.environ.get("DB_NAME", "medicalData")
DB_USER = os.environ.get("DB_USER", "user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")

# === FUNCTIONS ===

def get_db_connection():
    try:
        db_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(db_url)
        return engine.connect()
    except Exception as e:
        print(f"❌ DB connection failed: {e}")
        raise

def get_latest_vital_signs(patient_id, conn, limit=6):
    query = text("""
        SELECT hr, rr, body_temperature, spo2, gsr
        FROM vital_signs
        WHERE patient_id = :pid
        ORDER BY measurement_time DESC
        LIMIT :limit
    """)
    df = pd.read_sql(query, conn, params={"pid": patient_id, "limit": limit})
    df = df.iloc[::-1].reset_index(drop=True)
    return df


def predict_risk(patient_id):
    # Loading model and scalers
    model = tf.keras.models.load_model('model.keras')
    scaler_X = joblib.load("scaler_x.pkl")
    scaler_Y = joblib.load("scaler_y.pkl")

    conn = get_db_connection()
    try:
        # Get latest 6 vital signs for patient
        data = get_latest_vital_signs(patient_id, conn, limit=6)

        if data.shape[0] < 6:
            print(f"⚠️ Not enough data for patient {patient_id} to predict risk.")
            return None

        features = ["hr", "rr", "body_temperature", "spo2", "gsr"]        x = data[features].values

        # Scale features
        x_scaled = scaler_X.transform(x)
        # reshape for LSTM input: (1, time_steps, features)
        x_input = np.expand_dims(x_scaled, axis=0)

        # predict risk (scaled)
        y_pred_scaled = model.predict(x_input)
        # inverse transform to original scale
        y_pred = scaler_Y.inverse_transform(y_pred_scaled)

        # RISK LEVEL
        risk_level = y_pred[0][0]
        return risk_level
    finally:
        conn.close()


def main(patient_id):
    risk_level = predict_risk(patient_id)
    if risk_level is not None:
        print(f"✅ Predicted Risk Level for patient {patient_id}: {risk_level:.1f}")


# === MAIN ===
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"⏳ Usage: python predict_risk.py <patient_id>")
    else:
        patient_id = sys.argv[1]
        main(patient_id)