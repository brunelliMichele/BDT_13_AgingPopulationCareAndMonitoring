# process_patient_data.py module for processing clinical data

import logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
import pandas as pd
import numpy as np
import random
from sqlalchemy import text
import joblib
from tensorflow.keras.models import load_model
from sklearn.preprocessing import StandardScaler
import numpy as np
import os

# === GLOBAL VARIABLES ===
MODEL_PATH = os.path.join(os.getcwd(), "output", "model.keras")
SCALER_X_PATH = os.path.join(os.getcwd(), "output", "scaler_x.pkl")
SCALER_Y_PATH = os.path.join(os.getcwd(), "output", "scaler_y.pkl")

# === FUNCTIONS ===

# Simulate realistic body temperature data with mean 36.8°C and clip extreme values
def simulate_body_temperature(group):
    group = group.copy()
    body_temp = np.random.normal(loc=36.8, scale=0.3, size=len(group))
    body_temp = np.clip(body_temp, 35.5, 39.0)
    group['body_temperature'] = np.round(body_temp, 1)
    return group

# Generate realistic SpO2 values based on probability thresholds, mimicking elderly ranges
def generate_spo2_elderly():
    prob = random.random()
    if prob < 0.60:
        return round(random.uniform(93, 96), 1)
    elif prob < 0.95:
        return round(random.uniform(91, 92.9), 1)
    else:
        return round(random.uniform(87, 90.9), 1)

# Generate realistic GSR values using a Gaussian distribution
def generate_gsr_elderly():
    baseline = random.gauss(3, 1.2)
    return round(max(0.5, min(baseline, 6)), 2)

# Assign generated SpO2 and GSR values to each observation in the group
def simulate_spo2_gsr(group):
    group = group.copy()
    group['SpO2'] = [generate_spo2_elderly() for _ in range(len(group))]
    group['GSR'] = [generate_gsr_elderly() for _ in range(len(group))]
    return group

# Main function: extracts and processes observation data, then computes risk scores if enabled
def process_observations(engine, after_inserted_at=None, patient_ids=None, use_model=True):
    query = """
        SELECT date, patient AS patient_id, description, value, category
        FROM observations
        WHERE category IN ('vital-signs', 'survey')
          AND (description ILIKE '%Heart rate%' OR description ILIKE '%Respiratory rate%')
    """

    if patient_ids:
        placeholders = ','.join(f"'{pid}'" for pid in patient_ids)
        query += f" AND patient IN ({placeholders})"
        
    with engine.connect() as connection:
        df = pd.read_sql(sql=text(query), con=connection)

    if df.empty:
        return pd.DataFrame()

    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[["date", "patient_id", "description", "value"]]
    df["date"] = pd.to_datetime(df["date"])

    pivot_df = df.pivot_table(index=["patient_id", "date"], columns="description", values="value").reset_index()
    pivot_df.columns.name = None

    pivot_df = pivot_df.rename(columns={"Heart rate": "HR", "Respiratory rate": "RR"})
    pivot_df = pivot_df.sort_values(["patient_id", "date"]).reset_index(drop=True)

    pivot_df = pivot_df.groupby("patient_id", group_keys=False).apply(simulate_body_temperature).reset_index(drop=True)
    pivot_df = pivot_df.groupby("patient_id", group_keys=False).apply(simulate_spo2_gsr).reset_index(drop=True)

    pivot_df.dropna(inplace=True)

    if not use_model:
        logging.warning("🧪 Returning pivot_df without applying ML model.")
        return pivot_df

    # Apply machine learning model to compute risk levels per patient
    if use_model:
        model = load_model(MODEL_PATH)
        scaler_x = joblib.load(SCALER_X_PATH)
        scaler_y = joblib.load(SCALER_Y_PATH)

        features = ["HR", "RR", "body_temperature", "SpO2", "GSR"]
        risk_levels = []

        for patient_id, group in pivot_df.groupby("patient_id"):
            group = group.sort_values("date")
            x = group[features].values

            if len(x) < 6:
                continue  # skip if there isn't enough data

            x_scaled = scaler_x.transform(x)
            for i in range(5, len(x)):
                seq = x_scaled[i-5:i+1]  
                seq = np.expand_dims(seq, axis=0) 
                # Predict risk and adjust values to simulate variability among patients
                pred = model.predict(seq)
                risk = scaler_y.inverse_transform(pred)[0][0]

                if random.random() < 0.1:
                    risk -= random.uniform(10, 25)
                elif random.random() < 0.2:
                    risk += random.uniform(10, 25)
                else:
                    risk += random.uniform(-5, 5)
                risk_levels.append((patient_id, group.iloc[i]["date"], round(risk, 2)))
        if not risk_levels:
            return pd.DataFrame()

        # Merge predicted risk scores back into the pivoted DataFrame
        risk_df = pd.DataFrame(risk_levels, columns=["patient_id", "date", "risk_level"])
        pivot_df = pivot_df.merge(risk_df, on=["patient_id", "date"], how="inner")

        return pivot_df