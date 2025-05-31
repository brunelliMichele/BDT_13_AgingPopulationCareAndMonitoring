from pathlib import Path
import pandas as pd
import numpy as np 
from flask_app.db import get_db_connection
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dropout, Dense
from tensorflow.keras.callbacks import EarlyStopping
from sqlalchemy import create_engine
import joblib
import os
import random

# === PATHS ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model_path = os.path.join(BASE_DIR, "model.keras")
scaler_x_path = os.path.join(BASE_DIR, "scaler_x.pkl")
scaler_y_path = os.path.join(BASE_DIR, "scaler_y.pkl")

# === FUNCTIONS ===
def create_sequences(x, y, window_size = 6):
    x_seq, y_seq = [], []
    for i in range(len(x) - window_size):
        x_seq.append(x[i:i+window_size])
        y_seq.append(y[i+window_size])
    return np.array(x_seq), np.array(y_seq)

def simulate_body_temperature(group):
    group = group.copy()
    body_temp = np.random.normal(loc=36.8, scale=0.3, size=len(group))
    body_temp = np.clip(body_temp, 35.5, 39.0)
    group['Body Temperature'] = np.round(body_temp, 1)
    return group

def generate_spo2_elderly():
    prob = random.random()
    if prob < 0.60:
        return round(random.uniform(93, 96), 1)
    elif prob < 0.95:
        return round(random.uniform(91, 92.9), 1)
    else:
        return round(random.uniform(87, 90.9), 1)

def generate_gsr_elderly():
    baseline = random.gauss(3, 1.2)
    return round(max(0.5, min(baseline, 6)), 2)

def simulate_spo2_gsr(group):
    group = group.copy()
    group['SpO2'] = [generate_spo2_elderly() for _ in range(len(group))]
    group['GSR'] = [generate_gsr_elderly() for _ in range(len(group))]
    return group

def evaluate_risk_advanced(row):
    risk_score = 2
    spo2 = row['SpO2']
    gsr = row['GSR']
    hr = row['HR']
    rr = row['RR']
    body_temp = row['Body Temperature']

    if spo2 < 90:
        risk_score += 6
    elif spo2 < 91:
        risk_score += 5
    elif spo2 < 93:
        risk_score += 3
    elif spo2 < 95:
        risk_score += 1
    elif spo2 > 97:
        risk_score += 1

    if gsr < 0.8:
        risk_score += 5
    elif gsr < 1.0:
        risk_score += 3
    elif gsr < 1.5:
        risk_score += 1
    elif gsr > 5.5:
        risk_score += 2

    if hr < 45 or hr > 120:
        risk_score += 6
    elif hr < 50 or hr > 110:
        risk_score += 4
    elif hr < 60 or hr > 100:
        risk_score += 2
    elif hr < 65 or hr > 95:
        risk_score += 1

    if rr < 8 or rr > 30:
        risk_score += 6
    elif rr < 10 or rr > 24:
        risk_score += 4
    elif rr < 12 or rr > 20:
        risk_score += 2

    if body_temp < 35.0 or body_temp > 39.0:
        risk_score += 5
    elif body_temp < 35.5 or body_temp > 38.5:
        risk_score += 3
    elif body_temp < 36.0 or body_temp > 38.0:
        risk_score += 1

    max_score = 32
    risk_percentage = (risk_score / max_score) * 100
    return round(risk_percentage, 1)

def load_training_data(after_date=None):
    conn = get_db_connection()
    query = """
        SELECT "DATE", "PATIENT", "DESCRIPTION", "VALUE", "CATEGORY"
        FROM observation
        WHERE "CATEGORY" IN ('vital-signs', 'survey')
          AND ("DESCRIPTION" ILIKE '%Heart rate%' OR "DESCRIPTION" ILIKE '%Respiratory rate%')
    """
    if after_date:
        query += f" AND \"DATE\" > '{after_date.strftime('%Y-%m-%d %H:%M:%S')}'"
    df = pd.read_sql(query, conn)
    conn.close()

    df["VALUE"] = pd.to_numeric(df["VALUE"], errors='coerce')
    df = df[["DATE", "PATIENT", "DESCRIPTION", "VALUE"]]
    df["DATE"] = pd.to_datetime(df["DATE"])

    pivot_df = df.pivot_table(index=["PATIENT", "DATE"], columns="DESCRIPTION", values="VALUE").reset_index()
    pivot_df.columns.name = None
    pivot_df = pivot_df.rename(columns={"Heart rate": "HR", "Respiratory rate": "RR"})
    pivot_df = pivot_df.sort_values(["PATIENT", "DATE"]).reset_index(drop=True)

    pivot_df = pivot_df.groupby("PATIENT", group_keys=False).apply(simulate_body_temperature)
    pivot_df = pivot_df.groupby("PATIENT", group_keys=False).apply(simulate_spo2_gsr)
    pivot_df.dropna(inplace=True)
    pivot_df["Risk Level"] = pivot_df.apply(evaluate_risk_advanced, axis=1)

    return pivot_df

def main():
    LAST_TRAINING_FILE = Path("last_training_date.txt")
    last_training_date = None
    if LAST_TRAINING_FILE.exists():
        last_training_date = pd.to_datetime(LAST_TRAINING_FILE.read_text().strip())

    df = load_training_data(after_date=last_training_date)
    if df.empty:
        print("No new data available. Skipping training.")
        return

    x_data = df[["HR", "RR", "Body Temperature", "SpO2", "GSR"]].values
    y_data = df[["Risk Level"]].values

    scaler_x = MinMaxScaler()
    scaler_y = MinMaxScaler()
    x_scaled = scaler_x.fit_transform(x_data)
    y_scaled = scaler_y.fit_transform(y_data)

    x_seq, y_seq = create_sequences(x_scaled, y_scaled, window_size = 6)
    x_train, x_test, y_train, y_test = train_test_split(x_seq, y_seq, test_size = 0.2, random_state = 42)

    model = Sequential()
    model.add(LSTM(128, return_sequences = True, input_shape = (x_train.shape[1], x_train.shape[2])))
    model.add(Dropout(0.3))
    model.add(LSTM(64))
    model.add(Dropout(0.3))
    model.add(Dense(1, activation = "linear"))
    model.compile(optimizer = "adam", loss = "mse", metrics = ["mae"])
    model.fit(x_train, y_train, epochs=50, batch_size=128, validation_data = (x_test, y_test), callbacks = [EarlyStopping(patience = 5, restore_best_weights = True)], verbose = 1)
    
    # save model and scalers
    model.save(model_path)
    joblib.dump(scaler_x, scaler_x_path)
    joblib.dump(scaler_y, scaler_y_path)

    engine = create_engine("postgresql://your_username:your_password@localhost:5432/your_db_name")
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vital_signs_table (
                    "patient" TEXT,
                    "date" TIMESTAMP,
                    "HR" FLOAT,
                    "RR" FLOAT,
                    "Body Temperature" FLOAT,
                    "SpO2" FLOAT,
                    "GSR" FLOAT,
                    "Risk Level" FLOAT
                );
            """)

    df_to_save = df[["patient", "date", "HR", "RR", "Body Temperature", "SpO2", "GSR", "Risk Level"]]
    df_to_save.to_sql("vital_signs_table", con=engine, if_exists="replace", index=False)

    latest_date = df["DATE"].max()
    LAST_TRAINING_FILE.write_text(str(latest_date))

# === MAIN ===
if __name__ == "__main__":
    main()