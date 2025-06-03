# routes.py
from flask import render_template
from db import get_all_patients, get_city_avg_coords, get_patient_by_id, get_risk_level_by_id, get_all_risk_level

def register_routes(app):
    @app.route("/")
    def dashboard():
        patients = get_all_patients()
        city_coords = get_city_avg_coords(patients=patients)
        cities = sorted(set(p["city"] for p in patients))
        risk_levels = get_all_risk_level()
        for patient in patients:
            pid = patient["id"]
            patient["risk_level"] = risk_levels.get(pid)
        return render_template("index.html", patients=patients, city_coords=city_coords, cities=cities)
    
    # set route for patient detail page
    @app.route("/patient/<string:patient_id>")
    def patient_detail(patient_id):
        patient_data = get_patient_by_id(patient_id)
        try:
            risk_level = get_risk_level_by_id(patient_id)
            risk_level = float(risk_level) if risk_level is not None else None
        except Exception as e:
            print(f"⚠️ Errore durante il recupero del risk_level: {e}")
            risk_level = None

        if patient_data:
            return render_template("patient.html", patient = patient_data, risk_level = risk_level)
        else:
            return (f"No patient with ID {patient_id}", 404)