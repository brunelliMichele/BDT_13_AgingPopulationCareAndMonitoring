# BDT_13_AgingPopulationCareAndMonitoring
Design and prototype a big data system to assist caregivers and healthcare providers in supporting the elderly. Collect data from wearable health monitors, smart home sensors (motion detection, fridge usage, etc.), and medical records.


## Potential Data Sources:
1. [MIMIC-III Clinical Database](https://physionet.org/content/mimiciii/1.4/)
- ICU Dataset 
    - Contains data from 40,000+ ICU patients (2001–2012)
    - ~58,000 hospital stays
    - hourly vitals (heart rate, blood pressure), lab tests, medications, procedures, doctor/nurse notes, imaging reports, and survival data
- Relational database (26 linked tables) 
    - IDs tracking patients, admissions, ICU stays, etc. Includes tables like `admissions` (demographics), `chartevents` (vitals), `labevents` (test results), and free-text notes (discharge summaries, radiology reports).  
- Requires signing a data agreement + basic ethics training (CITI course). Free to use once approved—common process for medical data


2. [Synthetic Patient Population Simulator](https://github.com/synthetichealth/synthea)
- Open-source tool simulating *virtual patient lifespans* (birth to death) using clinical guidelines. 
- Outputs structured data (FHIR, CSV) with demographics, diagnoses (ICD-10), meds (RxNorm), labs (LOINC), encounters, and social determinants.  
- Generates massive datasets (millions of synthetic patients) for ML/AI training (e.g., predictive models, EHR interoperability testing) without privacy constraints
- Customizable modules simulate diseases, regional trends, or rare conditions.  
- Use API or export scripts to stream FHIR/JSON data directly into pipelines (e.g., Kafka, Flink) or cloud platforms (AWS Kinesis, GCP Pub/Sub). Enables real-time analytics, synthetic EHR testing, or digital twin simulations.  
- Freely downloadable (GitHub)  