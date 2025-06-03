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
import random

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
    try:
        db_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        return create_engine(db_url)
    except Exception as e:
        print(f"❌ Failed to create SQLAlchemy engine: {e}")
        raise


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
    group['body_temperature'] = np.round(body_temp, 1)
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
    body_temp = row['body_temperature']

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
    engine = get_db_engine()
    query = """
        SELECT date, patient AS patient_id, description, value, category
        FROM observations
        WHERE category IN ('vital-signs', 'survey')
          AND (description ILIKE '%Heart rate%' OR description ILIKE '%Respiratory rate%')
    """
    if after_date:
        query += f" AND \"date\" > '{after_date.strftime('%Y-%m-%d %H:%M:%S')}'"
    with engine.connect() as connection:
        df = pd.read_sql(sql=text(query), con=connection)

    if df.empty:
        print("⚠️ Nessun dato trovato nella query.")
        return pd.DataFrame()

    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[["date", "patient_id", "description", "value"]]
    df["date"] = pd.to_datetime(df["date"])
    # print(f"📊 Step 1 - Dati iniziali: {df.shape}")

    pivot_df = df.pivot_table(index=["patient_id", "date"], columns="description", values="value").reset_index()
    pivot_df.columns.name = None
    # print(f"📊 Step 2 - Dopo pivot: {pivot_df.shape}")

    pivot_df = pivot_df.rename(columns={"Heart rate": "HR", "Respiratory rate": "RR"})
    pivot_df = pivot_df.sort_values(["patient_id", "date"]).reset_index(drop=True)
    # print(f"📊 Step 3 - Dopo ordinamento: {pivot_df.shape}")

    # Ensure "patient_id" is not both index and column
    if "patient_id" in pivot_df.index.names:
        pivot_df = pivot_df.reset_index()

    pivot_df = pivot_df.groupby("patient_id", group_keys=False).apply(simulate_body_temperature).reset_index(drop=True)
    # print(f"📊 Step 4 - Dopo simulazione temperatura: {pivot_df.shape}")

    pivot_df = pivot_df.groupby("patient_id", group_keys=False).apply(simulate_spo2_gsr).reset_index(drop=True)
    # print(f"📊 Step 5 - Dopo simulazione SpO2 e GSR: {pivot_df.shape}")

    pivot_df.dropna(inplace=True)
    # print(f"📊 Step 6 - Dopo dropna: {pivot_df.shape}")

    # print("🔍 Checking Risk Level return types:")
    test_results = pivot_df.apply(lambda row: evaluate_risk_advanced(row), axis=1)
    # print(test_results.apply(type).value_counts())

    if not test_results.empty and isinstance(test_results.iloc[0], (int, float)):
        pivot_df["risk_level"] = test_results.astype(float)
    else:
        print("⚠️ Nessun dato valido per calcolare il livello di rischio.")
        return pivot_df
    print("✅ Risk level evaluated.")

    return pivot_df

def main():
    LAST_TRAINING_FILE = Path(OUTPUT_DIR) / "last_training_date.txt"
    last_training_date = None
    if LAST_TRAINING_FILE.exists():
        last_training_date = pd.to_datetime(LAST_TRAINING_FILE.read_text().strip())

    df = load_training_data(after_date=last_training_date)
    if df.empty:
        # print("No new data available. Skipping training.")
        return

    x_data = df[["HR", "RR", "body_temperature", "SpO2", "GSR"]].values
    y_data = df[["risk_level"]].values

    scaler_x = MinMaxScaler()
    scaler_y = MinMaxScaler()
    x_scaled = scaler_x.fit_transform(x_data)
    y_scaled = scaler_y.fit_transform(y_data)

    x_seq, y_seq = create_sequences(x_scaled, y_scaled, window_size = 6)
    x_train, x_test, y_train, y_test = train_test_split(x_seq, y_seq, test_size = 0.2, random_state = 42)


    model = Sequential([
        Input(shape=(x_train.shape[1], x_train.shape[2])),
        LSTM(128, return_sequences=True),
        Dropout(0.3),
        LSTM(64),
        Dropout(0.3),
        Dense(1, activation="linear")
    ])
    model.compile(optimizer = "adam", loss = "mse", metrics = ["mae"])
    model.fit(x_train, y_train, epochs=50, batch_size=128, validation_data = (x_test, y_test), callbacks = [EarlyStopping(patience = 5, restore_best_weights = True)], verbose = 1)
    # print("✅ Training completed. Saving model and scalers...")
    
    # save model and scalers
    model.save(model_path)
    # print("✅ Model saved.")
    joblib.dump(scaler_x, scaler_x_path)
    joblib.dump(scaler_y, scaler_y_path)
    # print("✅ Scalers saved.")

    engine = get_db_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vital_signs (
                "patient_id" UUID REFERENCES patients(id),
                "date" TIMESTAMP,
                "HR" FLOAT,
                "RR" FLOAT,
                "body_temperature" FLOAT,
                "SpO2" FLOAT,
                "GSR" FLOAT,
                "risk_level" FLOAT,
                PRIMARY KEY ("patient_id", "date")
            );
        """))

    df_to_save = df[["patient_id", "date", "HR", "RR", "body_temperature", "SpO2", "GSR", "risk_level"]]
    with engine.connect() as conn:
        for _, row in df_to_save.iterrows():
            metadata = MetaData()
            vital_signs = Table("vital_signs", metadata, autoload_with=engine)
            stmt = insert(vital_signs).values(row.to_dict())
            stmt = stmt.on_conflict_do_nothing(index_elements=["patient_id", "date"])
            conn.execute(stmt)
    # print("✅ Data saved to vital_signs_table.")

    latest_date = df["date"].max()
    LAST_TRAINING_FILE.write_text(str(latest_date))
    print(f"✅ Training complete. Last training date saved: {latest_date}")

# === MAIN ===
if __name__ == "__main__":
    main()