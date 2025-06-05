import subprocess
import os
import time

# === CONFIG ===
SYNTHEA_DIR = "/app/synthea"
STATE = os.getenv("SYNTHEA_STATE", "Massachusetts")
PATIENTS = int(os.getenv("SYNTHEA_PATIENTS", 5))
CONFIG_PATH = os.getenv("SYNTHEA_CONFIG", "/app/config.json")
INTERVAL = int(os.getenv("GENERATE_INTERVAL", 300))  # seconds

def run_synthea():
    cmd = ["./run_synthea", STATE, "-p", str(PATIENTS), "-c", CONFIG_PATH]
    subprocess.run(cmd, cwd=SYNTHEA_DIR)

if __name__ == "__main__":
    while True:
        print("🚀 Avvio generazione dati Synthea...")
        run_synthea()
        print(f"⏱️ Attendo {INTERVAL} secondi prima del prossimo ciclo...")
        time.sleep(INTERVAL)