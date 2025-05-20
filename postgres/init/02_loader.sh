#!/bin/bash

# Variabili ambiente (opzionali se già fornite da Docker)
DB_NAME=${POSTGRES_DB:-medicalData}
DB_USER=${POSTGRES_USER:-user}

# Percorso dei file CSV (montato da host a /data nel docker-compose.yml)
CSV_DIR="/data"

# Lista dei file CSV e tabelle corrispondenti
CSV_FILES=("patients.csv" "organizations.csv" "providers.csv" "payers.csv" "encounters.csv" "allergies.csv" "careplans.csv" "claims.csv" "conditions.csv" "devices.csv" "imaging_studies.csv" "immunizations.csv" "medications.csv" "observations.csv" "procedures.csv" "supplies.csv")
TABLES=("PATIENTS" "ORGANIZATIONS" "PROVIDERS" "PAYERS" "ENCOUNTERS" "ALLERGIES" "CAREPLANS" "CLAIMS" "CONDITIONS" "DEVICES" "IMAGING_STUDIES" "IMMUNIZATIONS" "MEDICATIONS" "OBSERVATIONS" "PROCEDURES" "SUPPLIES")

# Importa ogni CSV nella tabella corrispondente
for i in "${!CSV_FILES[@]}"; do
  FILE="${CSV_FILES[$i]}"
  TABLE="${TABLES[$i]}"
  FILE_PATH="$CSV_DIR/$FILE"

  if [[ -f "$FILE_PATH" ]]; then
    echo "📥 Uploading $FILE into table $TABLE..."
    psql -U "$DB_USER" -d "$DB_NAME" -c "\copy $TABLE FROM '$FILE_PATH' WITH (FORMAT CSV, HEADER);"
  else
    echo "❌ File $FILE not found in $CSV_DIR — skipping $TABLE"
  fi
done

echo "✅ Import complete!"