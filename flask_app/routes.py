# routes.py

# Defines Flask routes for the dashboard and individual patient detail views.
# Fetches patient data and renders the appropriate templates.

import logging
from flask import render_template
from db import get_all_patients, get_city_avg_coords, get_patient_by_id, get_risk_level_by_id, get_all_risk_level, get_risk_trend_by_id, get_risk_trend_raw

def register_routes(app):
    # Dashboard route: shows overview of all patients and cities
    @app.route("/")
    def dashboard():
        # Retrieve all patients from the database
        patients = get_all_patients()
        # Calculate average coordinates per city for mapping
        city_coords = get_city_avg_coords(patients=patients)
        # Extract unique cities for filtering or display
        cities = sorted(set(p["city"] for p in patients))
        # Retrieve risk levels for all patients
        risk_levels = get_all_risk_level()
        # Assign risk level to each patient record
        for patient in patients:
            pid = str(patient["id"])
            patient["risk_level"] = risk_levels.get(pid)
        # Render the main dashboard template with patient and city data
        return render_template("index.html", patients=patients, city_coords=city_coords, cities=cities)
    
    # Patient detail route: shows detailed information and risk trends for a specific patient
    @app.route("/patient/<string:patient_id>")
    def patient_detail(patient_id):
        # Retrieve patient data by ID
        patient_data = get_patient_by_id(patient_id)
        risk_level = None
        risk_trend = {"dates": [], "values": []}
        risk_trend_raw = []

        if patient_data:
            # Attempt to retrieve risk information and trends for the patient
            try:
                risk_level = get_risk_level_by_id(patient_id)
                risk_level = float(risk_level) if risk_level is not None else None
                risk_trend = get_risk_trend_by_id(patient_id)
                risk_trend_raw = get_risk_trend_raw(patient_id)
            except Exception as e:
                logging.warning("Error retrieving risk level or trend data: %s", e)

            # Render the patient detail template with retrieved data
            return render_template("patient.html", patient=patient_data, risk_level=risk_level, risk_trend=risk_trend, risk_trend_raw=risk_trend_raw)
        else:
            # Return 404 if patient ID not found
            return (f"No patient with ID {patient_id}", 404)