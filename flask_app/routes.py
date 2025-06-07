# routes.py
import logging
from flask import render_template
from db import get_all_patients, get_city_avg_coords, get_patient_by_id, get_risk_level_by_id, get_all_risk_level, get_risk_trend_by_id, get_risk_trend_raw

def register_routes(app):
    @app.route("/")
    def dashboard():
        patients = get_all_patients()
        city_coords = get_city_avg_coords(patients=patients)
        cities = sorted(set(p["city"] for p in patients))
        risk_levels = get_all_risk_level()
        logging.info("Patient IDs: %s", [p["id"] for p in patients])
        logging.info("Risk Levels: %s", risk_levels)
        for patient in patients:
            pid = str(patient["id"])
            patient["risk_level"] = risk_levels.get(pid)
            logging.info("Patient %s -> Risk Level: %s", pid, patient["risk_level"])
        return render_template("index.html", patients=patients, city_coords=city_coords, cities=cities)
    
    # set route for patient detail page
    @app.route("/patient/<string:patient_id>")
    def patient_detail(patient_id):
        patient_data = get_patient_by_id(patient_id)
        risk_level = None
        risk_trend = {"dates": [], "values": []}
        risk_trend_raw = []

        if patient_data:
            try:
                risk_level = get_risk_level_by_id(patient_id)
                risk_level = float(risk_level) if risk_level is not None else None
                risk_trend = get_risk_trend_by_id(patient_id)
                risk_trend_raw = get_risk_trend_raw(patient_id)
            except Exception as e:
                logging.warning("Errore durante il recupero del risk_level o del trend: %s", e)

            return render_template("patient.html", patient=patient_data, risk_level=risk_level, risk_trend=risk_trend, risk_trend_raw=risk_trend_raw)
        else:
            return (f"No patient with ID {patient_id}", 404)