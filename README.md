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

  ------------------------------------------------------------------------------------------------
3. [Cerebromicrovascular Disease in Elderly with Diabetes] (https://physionet.org/content/cded/1.0.1/Data_Description/#files-panel)
   - Description: this database contains multimodal data from a large study investigating the effects of ischemic stroke on cerebral vasoregulation. The cross         sectional study compared 60 subjects who suffered strokes, to 60 control subjects, collecting the following data for each patient across multiple days.
   - Contains several medical parameters: age, height, mass, BMI, body composition, # glucose, # hemoglobin, etc
   - Pros: a lot of variables. Selection is needed
   - Cons: the number of patients is too low for training a ML, unless we use the dataset composition to iteravely produce synthetic data.
   - Freely downloadable (PhysioNet)
4. [Smart Home Dataset] (https://data.mendeley.com/datasets/zgsw84b2ff/1)
   - Description: 29 sensors are placed on carpets, doors, lights, bed, couch, fridge, oven, tv, and wardrobes. In addition to these sensors, the dataset also     
   contains the activity column that describes what activity (eat, sleep, work, personal, other, or anomaly) being simulated.
   Another column included in the dataset is the timestamps. This captures the time the sensor was activated and aggregated accordingly during the aggregation 
   phase of the simulation process.
   - CSV data containing binary and timestamp variables
   - Freely downloadable (Mendeley data)
6. [MQTT-Sensors linkage Github project] (https://github.com/glmorandi/mqtt-iot-sensor/tree/main)
   - Description: collects and visualizes simulated IoT sensor data (temperature, humidity, vibration, luminosity) with real-time monitoring, a web interface,     
     Discord webhook and MQTT.
   - Freely downloadable (GitHub)
