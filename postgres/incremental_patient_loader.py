import subprocess
import os
import logging
import time
from datetime import datetime, timezone, timedelta
import pandas as pd
from sqlalchemy import create_engine, text, Table, MetaData
from sqlalchemy.dialects.postgresql import insert
import sys

# add '/shared' directory to allow importing shared modules
sys.path.append("/shared")
from process_patient_data import process_observations

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# wait two minutes to start if set to 'true'
if os.getenv("DELAY_STARTUP", "false").lower() == "true":
    time.sleep(120)  # delay 2 minutes

# === CONFIG VARIABLES ===
SYNTHEA_DIR = "/app"
PATIENTS = 1
INTERVAL = int(os.getenv("GENERATE_INTERVAL", 300))
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = 5432
DB_NAME = os.getenv("DB_NAME", "medicalData")
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# create SQLAlchemy database engine
engine = create_engine(DB_URL)

# === FUNCTIONS ===
# return the time range for the current hour to tag patient generation sessions.
def today_range():
    now = datetime.now(timezone.utc)
    start = now.replace(minute=0, second=0, microsecond=0)
    stop = start + timedelta(hours=1)
    return start.isoformat(), stop.isoformat()

# load a synthea generated csv into a table in the db
def load_csv_to_db(filename, table_name):
    path = os.path.join(SYNTHEA_DIR, "output", "csv", filename)
    if not os.path.exists(path):
        return
    df = pd.read_csv(path)
    df.columns = [col.lower() for col in df.columns]
    if df.empty:
        return
    df.to_sql(table_name, con=engine, if_exists="append", index=False)

# get the last generated patients
def get_new_patient_ids():
    path = os.path.join(SYNTHEA_DIR, "output", "csv", "patients.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        if "id" in df.columns:
            return df["id"].dropna().unique().tolist()
    return []

# add vital signs records to the db
def insert_vital_signs(df):
    if df.empty:
        return

    df_to_save = df[["patient_id", "date", "HR", "RR", "body_temperature", "SpO2", "GSR", "risk_level"]].copy()
    df_to_save.columns = [col.lower() if col not in ("patient_id", "date", "risk_level") else col for col in df_to_save.columns]

    with engine.begin() as conn:
        metadata = MetaData()
        vital_signs = Table("vital_signs", metadata, autoload_with=conn)
        rows_inserted = 0
        for _, row in df_to_save.iterrows():
            stmt = insert(vital_signs).values(row.to_dict())
            stmt = stmt.on_conflict_do_nothing(index_elements=["patient_id", "date"])
            result = conn.execute(stmt)
            if result.rowcount == 1:
                rows_inserted += 1
    logging.info(f"✅ Inserted {rows_inserted} new rows into vital_signs.")

# generate new patients with synthea, load the csv in the db, extract IDs to populate vital signs df
def run_incremental_generation():
    start_time, stop_time = today_range()
    logging.info(f"✚ Generate {PATIENTS} new patients from {start_time} to {stop_time}")
    cmd = cmd = [
        "java", "-jar", "synthea-with-dependencies.jar",
        "-p", str(PATIENTS),
        "Massachusetts",
        "-a", "65-100",
        "-c", "custom.properties"
    ]
    subprocess.run(cmd, cwd=SYNTHEA_DIR)

    load_csv_to_db("patients.csv", "patients")
    load_csv_to_db("encounters.csv", "encounters")
    load_csv_to_db("providers.csv", "providers")
    load_csv_to_db("observations.csv", "observations")
    load_csv_to_db("conditions.csv", "conditions")

    patient_ids = get_new_patient_ids()
    df = process_observations(engine, patient_ids=patient_ids)
    insert_vital_signs(df)

# === MAIN ===
if __name__ == "__main__":
    # generate patients continuously at regular intervals
    while True:
        run_incremental_generation()
        logging.info(f"⏱️ Sleeping {INTERVAL} seconds before next patient...")
        time.sleep(INTERVAL)