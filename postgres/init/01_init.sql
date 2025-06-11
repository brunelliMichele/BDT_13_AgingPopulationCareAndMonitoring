BEGIN;

-- Create tables

CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY,
    birthdate DATE NOT NULL,
    deathdate DATE,
    ssn VARCHAR NOT NULL,
    drivers VARCHAR,
    passport VARCHAR,
    prefix VARCHAR,
    first VARCHAR NOT NULL,
    middle VARCHAR,
    last VARCHAR NOT NULL,
    suffix VARCHAR,
    maiden VARCHAR,
    marital VARCHAR,
    race VARCHAR NOT NULL,
    ethnicity VARCHAR NOT NULL,
    gender VARCHAR NOT NULL,
    birthplace VARCHAR NOT NULL,
    address VARCHAR NOT NULL,
    city VARCHAR NOT NULL,
    state VARCHAR NOT NULL,
    county VARCHAR,
    fips VARCHAR,
    zip VARCHAR,
    lat NUMERIC,
    lon NUMERIC,
    healthcare_expenses NUMERIC NOT NULL,
    healthcare_coverage NUMERIC NOT NULL,
    income NUMERIC NOT NULL
);

CREATE TABLE IF NOT EXISTS conditions (
    start DATE NOT NULL,
    stop DATE,
    patient UUID NOT NULL REFERENCES patients(id),
    encounter UUID NOT NULL,
    system VARCHAR NOT NULL,
    code VARCHAR NOT NULL,
    description VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS observations (
    date TIMESTAMP NOT NULL,
    patient UUID NOT NULL REFERENCES patients(id),
    encounter UUID,
    category VARCHAR,
    code VARCHAR NOT NULL,
    description VARCHAR NOT NULL,
    value VARCHAR NOT NULL,
    units VARCHAR,
    type VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    alert_type TEXT NOT NULL,
    room TEXT,
    message TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS vital_signs (
    patient_id UUID REFERENCES patients(id),
    date TIMESTAMP,
    hr FLOAT,
    rr FLOAT,
    body_temperature FLOAT,
    spo2 FLOAT,
    gsr FLOAT,
    risk_level FLOAT,
    inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (patient_id, date)
);

COMMIT;