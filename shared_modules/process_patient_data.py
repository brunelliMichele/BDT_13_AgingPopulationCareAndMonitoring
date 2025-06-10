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

# simulates body temperature data with realistic data
def simulate_body_temperature(group):
    group = group.copy()
    body_temp = np.random.normal(loc=36.8, scale=0.3, size=len(group))
    body_temp = np.clip(body_temp, 35.5, 39.0)
    group['body_temperature'] = np.round(body_temp, 1)
    return group

# generates realistic oxygen saturation (SpO2) data for older adults
def generate_spo2_elderly():
    prob = random.random()
    if prob < 0.60:
        return round(random.uniform(93, 96), 1)
    elif prob < 0.95:
        return round(random.uniform(91, 92.9), 1)
    else:
        return round(random.uniform(87, 90.9), 1)

# generates realistic galvanic skin response (GSR) data for older adults
def generate_gsr_elderly():
    baseline = random.gauss(3, 1.2)
    return round(max(0.5, min(baseline, 6)), 2)

# adds SpO2 and GSR (previously generated) to a patient
def simulate_spo2_gsr(group):
    group = group.copy()
    group['SpO2'] = [generate_spo2_elderly() for _ in range(len(group))]
    group['GSR'] = [generate_gsr_elderly() for _ in range(len(group))]
    return group

# # calculates a risk level from 0 to 100 for a patient
# def evaluate_risk_advanced(row):
#     risk_score = 2
#     spo2 = row['SpO2']
#     gsr = row['GSR']
#     hr = row['HR']
#     rr = row['RR']
#     body_temp = row['body_temperature']
#
#     if spo2 < 90:
#         risk_score += 6
#     elif spo2 < 91:
#         risk_score += 5
#     elif spo2 < 93:
#         risk_score += 3
#     elif spo2 < 95:
#         risk_score += 1
#     elif spo2 > 97:
#         risk_score += 1
#
#     if gsr < 0.8:
#         risk_score += 5
#     elif gsr < 1.0:
#         risk_score += 3
#     elif gsr < 1.5:
#         risk_score += 1
#     elif gsr > 5.5:
#         risk_score += 2
#
#     if hr < 45 or hr > 120:
#         risk_score += 6
#     elif hr < 50 or hr > 110:
#         risk_score += 4
#     elif hr < 60 or hr > 100:
#         risk_score += 2
#     elif hr < 65 or hr > 95:
#         risk_score += 1
#
#     if rr < 8 or rr > 30:
#         risk_score += 6
#     elif rr < 10 or rr > 24:
#         risk_score += 4
#     elif rr < 12 or rr > 20:
#         risk_score += 2
#
#     if body_temp < 35.0 or body_temp > 39.0:
#         risk_score += 5
#     elif body_temp < 35.5 or body_temp > 38.5:
#         risk_score += 3
#     elif body_temp < 36.0 or body_temp > 38.0:
#         risk_score += 1
#
#     max_score = 32
#     risk_percentage = (risk_score / max_score) * 100
#     return round(risk_percentage, 1)

# "main function" reads data from database and processes it using above functions, returns a dataframe to populate vital_signs table
def process_observations(engine, after_inserted_at=None, patient_ids=None, use_model=True):
    logging.info("📥 process_observations() called")
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
        logging.info("🧪 Returning pivot_df without applying ML model.")
        return pivot_df

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
                continue  # salta se non ci sono abbastanza dati

            x_scaled = scaler_x.transform(x)
            for i in range(5, len(x)):
                seq = x_scaled[i-5:i+1]  # finestra di 6 step
                seq = np.expand_dims(seq, axis=0)  # shape (1, 6, features)
                pred = model.predict(seq)
                risk = scaler_y.inverse_transform(pred)[0][0]
                if random.random() < 0.1:
                    # 10% dei pazienti stanno meglio → abbassa il rischio
                    risk -= random.uniform(10, 25)
                elif random.random() < 0.2:
                    # 10% dei pazienti stanno peggio → alza il rischio
                    risk += random.uniform(10, 25)
                else:
                    # tutti gli altri → variazione normale
                    risk += random.uniform(-5, 5)
                risk_levels.append((patient_id, group.iloc[i]["date"], round(risk, 2)))
        if not risk_levels:
            return pd.DataFrame()

        risk_df = pd.DataFrame(risk_levels, columns=["patient_id", "date", "risk_level"])
        pivot_df = pivot_df.merge(risk_df, on=["patient_id", "date"], how="inner")

        logging.info(f"📤 Returning pivot_df with shape: {pivot_df.shape}")
        return pivot_df