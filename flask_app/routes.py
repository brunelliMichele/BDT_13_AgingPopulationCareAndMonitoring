# routes.py
from flask import render_template
from db import get_all_patients, get_city_avg_coords, get_patient_by_id, get_risk_level_by_id, get_all_risk_level, get_risk_trend_by_id, get_risk_trend_raw

def register_routes(app):
    @app.route("/")
    def dashboard():
        patients = get_all_patients()
        city_coords = get_city_avg_coords(patients=patients)
        cities = sorted(set(p["city"] for p in patients))
        risk_levels = get_all_risk_level()
        print("➕ Patient IDs:", [p["id"] for p in patients])
        print("📊 Risk Levels:", risk_levels)
        for patient in patients:
            pid = str(patient["id"])
            patient["risk_level"] = risk_levels.get(pid)
            print(f"Patient {pid} -> Risk Level: {patient['risk_level']}")
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
                print(f"⚠️ Errore durante il recupero del risk_level o del trend: {e}")

            return render_template("patient.html", patient=patient_data, risk_level=risk_level, risk_trend=risk_trend, risk_trend_raw=risk_trend_raw)
        else:
            return (f"No patient with ID {patient_id}", 404)