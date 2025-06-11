# inital_population.py

# Script to run Synthea for generating synthetic patient data and load it into a PostgreSQL database.
# It generates data using configured parameters and populates key tables: patients, observations and conditions.

import logging
import subprocess
import os
import pandas as pd
from sqlalchemy import create_engine

# === CONFIG VARIABLES ===
SYNTHEA_DIR = "/app"
PATIENTS = int(os.getenv("SYNTHEA_PATIENTS", 100))
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = 5432
DB_NAME = os.getenv("DB_NAME", "medicalData")
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DB_URL)

# === FUNCTIONS ===

# Load a specified CSV file into a target PostgreSQL table
def load_csv_to_db(filename, table_name):
    path = os.path.join(SYNTHEA_DIR, "output", "csv", filename)
    if not os.path.exists(path):
        logging.warning(f"⚠️ File {filename} not found.")
        return
    df = pd.read_csv(path)
    df.columns = [col.lower() for col in df.columns]
    if df.empty:
        logging.warning(f"⚠️ No data to load in {filename}.")
        return
    df.to_sql(table_name, con=engine, if_exists="append", index=False)
    logging.debug(f"✅ Loaded {len(df)} rows into '{table_name}' table.")

# Run Synthea to generate synthetic data and load selected CSVs into the database
def run_synthea():
    cmd = [
        "java", "-jar", "synthea-with-dependencies.jar",
        "-p", str(PATIENTS),
        "Massachusetts",
        "-a", "65-100",
        "-c", "custom.properties"
    ]

    if not os.path.exists(SYNTHEA_DIR):
        logging.error(f"❌ Synthea directory not found: {SYNTHEA_DIR}")
        return
    
    subprocess.run(cmd, cwd=SYNTHEA_DIR)
    

    # Load generated CSVs into the database
    load_csv_to_db("patients.csv", "patients")
    load_csv_to_db("observations.csv", "observations")
    load_csv_to_db("conditions.csv", "conditions")

# Entry point for the script
if __name__ == "__main__":
    run_synthea()