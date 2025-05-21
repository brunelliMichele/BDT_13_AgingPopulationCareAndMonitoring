# routes.py
from flask import render_template
from db import get_all_patients, get_city_avg_coords, get_patient_by_id

def register_routes(app):
    @app.route("/")
    def dashboard():
        patients = get_all_patients()
        city_coords = get_city_avg_coords(patients=patients)
        cities = sorted(set(p["city"] for p in patients))
        return render_template("index.html", patients=patients, city_coords=city_coords, cities=cities)
    
    # set route for patient detail page
    @app.route("/patient/<string:patient_id>")
    def patient_detail(patient_id):
        patient_data = get_patient_by_id(patient_id)

        if patient_data:
            return render_template("patient.html", patient = patient_data)
        else:
            return (f"No patient with ID {patient_id}", 404)