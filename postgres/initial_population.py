import logging
import subprocess
import os
import pandas as pd
from sqlalchemy import create_engine
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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
    logging.info(f"✅ Loaded {len(df)} rows into '{table_name}' table.")

def run_synthea():
    cmd = [
        "java", "-jar", "synthea-with-dependencies.jar",
        "-p", str(PATIENTS),
        "Massachusetts",
        "-a", "65-100",
        "-c", "custom.properties"
    ]

    if not os.path.exists(SYNTHEA_DIR):
        logging.error(f"❌ Directory Synthea non trovata: {SYNTHEA_DIR}")
        logging.error(f"📂 Contenuto /app: {os.listdir('/app')}")
        return
    
    subprocess.run(cmd, cwd=SYNTHEA_DIR)
    
    if not os.path.exists("/app"):
        logging.warning("⚠️ La directory /app non esiste.")

    # Load generated CSVs into the database
    load_csv_to_db("patients.csv", "patients")
    load_csv_to_db("encounters.csv", "encounters")
    load_csv_to_db("providers.csv", "providers")
    load_csv_to_db("observations.csv", "observations")
    load_csv_to_db("conditions.csv", "conditions")



# === MAIN ===
if __name__ == "__main__":
    logging.info("🚀 Starting initial patient generation with Synthea...")
    run_synthea()
    logging.info("✅ Generation completed successfully.")