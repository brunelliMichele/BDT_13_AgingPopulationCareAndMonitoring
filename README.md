# ToDo RightNow


# Project Requirements
## Description 
This repository contains the Caregiver Assistance and Remote Elderly Supervision (CARES) System developed by group 13. The project aims to assist caregivers and healthcare providers in supporting the elderly, by collecting data from smart home sensors, medical records and wearable health monitors. Real-time analytics are constantly sift through LSTM model to detect changes in daily routines and health indicators, triggering alerts for potential emergencies. 

## Abstract
XXX

## Technologies used

- **PostgreSQL:** RDMS used to implement databases to store the raw and processed medical data and smart home sensors data;
- **Apache Kafka:** Used to implement publish/subscribe model, specifying the topic within the data pipeline and connecting the different components of the system;
- **Docker + Docker Compose:** Multiple containers singularly developed in Docker are orchestrated and managed together in Docker Compose;
- **Flask:** Python framework used to develop the backend and API for the User Interface. The subject can see in real-time the activities of sensors and the current and past clinical conditions of the elderly patient, along with potential alerts and the actual health risk;
- **WebSocket (via Flask-SocketIO):** Enables real-time communication between backend and frontend for immediate delivery of alerts and live sensor updates.
- **JavaScript (Vanilla JS, Chart.js, Leaflet):** Used to build a responsive frontend interface, visualize patient data over time (Chart.js), and display geographical information such as patient or alert locations (Leaflet);
- **Tailwind CSS:** Utility-first CSS framework used to design a clean, responsive, and customizable user interface for the dashboard and alert visualization.

## System Architecture

![System Architecture](images/system_architecture.png)

## Project Structure

The repository is organized as follows:

```
.
├── docker-compose.yml
├── flask_app
│   ├── app.py
│   ├── config.py
│   ├── db.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── routes.py
│   ├── sockets.py
│   ├── static
│   │   ├── css
│   │   │   └── style.css
│   │   ├── favicon.ico
│   │   └── js
│   │       ├── alerts.js
│   │       ├── main.js
│   │       ├── map.js
│   │       ├── patient_chart.js
│   │       ├── patient_main.js
│   │       ├── ui.js
│   │       └── utils.js
│   └── templates
│       ├── index.html
│       └── patient.html
├── kafka
│   ├── Dockerfile
│   ├── house_data.json
│   ├── requirements.txt
│   ├── risk_level_producer.py
│   └── smart_data_producer.py
├── ml_model
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── output
│   │   ├── model.keras
│   │   ├── scaler_x.pkl
│   │   └── scaler_y.pkl
│   ├── requirements.txt
│   ├── train_loop.py
│   └── train_model.py
├── postgres
│   ├── Dockerfile
│   ├── incremental_patient_loader.py
│   ├── init
│   │   └── 01_init.sql
│   ├── initial_population.py
│   ├── ReadMe.md
│   ├── requirements.txt
│   └── synthea-with-dependencies.jar
├── project_structure.txt
├── ProjectIdeas.md
├── README.md
└── shared_modules
    └── process_patient_data.py
```

## Setup & Configuration

### Docker Setup

The project uses Docker to manage and run services. It includes a Docker Compose file docker-compose.yml which sets up PostgreSQL, Kafka, Flask and other servicies for generate and process the data. 

### 📦 Large File Support

This project uses [Git LFS](https://git-lfs.github.com/) for managing large files (e.g., model weights).

1. **Before cloning or pulling:**
    ```sh
    git lfs install
    ```
2. **If you already cloned the repo without LFS, run:**
    ```sh
    git lfs pull
    ```

### How to Run

1. **Start Docker:**
    ```sh
    docker-compose up --build [-d]
    ```
2. **Access to the dashboard:**
    Open a browser and go to `http://localhost:8000`.

3. **To restart the project:**
    Clean up with:
    ```sh
    docker-compose down -v --remove-orphans
    ```
    So rebuild and relaunch (1)


## Components Description
### UI
![UI-WireFrame](images/WireFrame.png)

## Database
XXX
## Kafka
XXX
## Flask
XXX

## Data Sources:
[Synthetic Patient Population Simulator](https://github.com/synthetichealth/synthea)
- Open-source tool simulating *virtual patient lifespans* (birth to death) using clinical guidelines. 
- Outputs structured data (FHIR, CSV) with demographics, diagnoses (ICD-10), meds (RxNorm), labs (LOINC), encounters, and social determinants.  
- Generates massive datasets (millions of synthetic patients) for ML/AI training (e.g., predictive models, EHR interoperability testing) without privacy constraints
- Customizable modules simulate diseases, regional trends, or rare conditions.  
- Use API or export scripts to stream FHIR/JSON data directly into pipelines (e.g., Kafka, Flink) or cloud platforms (AWS Kinesis, GCP Pub/Sub). Enables real-time analytics, synthetic EHR testing, or digital twin simulations.  
- Freely downloadable (GitHub)


### Authors
This project was created by group 13, consisting of:
 - Luca Frank - [@Luca-Frank](https://github.com/Luca-Frank)
 - Antonio Mazzarello - [@Mazza00](https://github.com/Mazza00)
 - Michele Brunelli - [@brunelliMichele](https://github.com/brunelliMichele)
 - Francesco Danesi - [@FrancescoDanesi126](https://github.com/Francescodanesi126)
