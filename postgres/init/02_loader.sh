#!/bin/bash
# Postgres container name
CONTAINER_NAME=bdt_13-db-1


DB_NAME=medicalData
DB_USER=user
# add here csv file names and table name for the db
CSV_FILES=("patients.csv" "organizations.csv" "providers.csv" "payers.csv" "encounters.csv" "allergies.csv" "careplans.csv" "claims.csv" "conditions.csv" "devices.csv" "imaging_studies.csv" "immunizations.csv" "medications.csv" "observations.csv" "procedures.csv" "supplies.csv")
TABLES=("PATIENTS" "ORGANIZATIONS" "PROVIDERS" "PAYERS" "ENCOUNTERS" "ALLERGIES" "CAREPLANS" "CLAIMS" "CONDITIONS" "DEVICES" "IMAGING_STUDIES" "IMMUNIZATIONS" "MEDICATIONS" "OBSERVATIONS" "PROCEDURES" "SUPPLIES")

# copy the csv file from local to the docker container
for FILE in "${CSV_FILES[@]}"; do
  echo "📁 Copying $FILE in the container..."
  docker cp ./postgres/data/$FILE $CONTAINER_NAME:/tmp/$FILE
done

# populate the database
for i in "${!CSV_FILES[@]}"; do
  FILE=${CSV_FILES[$i]}
  TABLE=${TABLES[$i]}

  echo "📥 Upload $FILE in table $TABLE..."

  docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "\copy $TABLE FROM '/tmp/$FILE' WITH (FORMAT CSV, HEADER);"
done

echo "✅ Import complete!"
