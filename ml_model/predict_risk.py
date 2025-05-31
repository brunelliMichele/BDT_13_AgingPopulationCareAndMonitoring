import pandas as pd
import numpy as np
import tensorflow as tf
import joblib
import psycopg2
import sys
import os
from sqlalchemy import create_engine, text
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from flask_app.db import get_db_connection

# === FUNCTIONS ===
def get_latest_vital_signs(patient_id, conn, limit=6):
    query = f""" SELECT 'HR', 'RR', 'Body Temperature', 'SpO2', 'GSR' FROM vital_signs_table WHERE patient_id = %s ORDER BY measurement_time DESC LIMIT %s"""

    df = pd.read_sql(query, conn, params=(patient_id, limit))
    df = df.iloc[::-1].reset_index(drop=True)

    return df


def main(patient_id):
    # Loading model and scalers
    model = tf.keras.models.load_model('model.keras')
    scaler_X = joblib.load("scaler_x.pkl")
    scaler_Y = joblib.load("scaler_y.pkl")

    conn = get_db_connection()
    
    # Get latest 6 vital signs for patient
    data = get_latest_vital_signs(patient_id, conn, limit = 6)

    if data.shape[0] < 6:
        print(f"⚠️ Not enough data for patient {patient_id} to predict risk.")
        return

    features = ["HR", "RR", "Body Temperature", "SpO2", "GSR"]
    x = data[features].values

    # Scale features
    x_scaled = scaler_X.transform(x)
    # reshape for LSTM input: (1, time_steps, features)
    x_input = np.expand_dims(x_scaled, axis = 0)

    # predict risk (scaled)
    y_pred_scaled = model.predict(x_input)
    # inverse transform to original scale
    y_pred = scaler_Y.inverse_transform(y_pred_scaled)

    # RISK LEVEL
    risk_level = y_pred[0][0]
    print(f"✅ Predicted Risk Level for patient {patient_id}: {risk_level:.1f}")

    conn.close()


# === MAIN ===
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"⏳ Usage: python predict_risk.py <patient_id>")
    else:
        patient_id = sys.argv[1]
        main(patient_id)