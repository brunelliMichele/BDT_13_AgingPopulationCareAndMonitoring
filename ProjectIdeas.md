## Project Idea
**Smart Elderly Home Monitoring System**^^
- Simulate a connected elderly home: wearable + smart home sensor data
- Build an end-to-end big data pipeline  
- Simulate realistic streaming data at scale 
- Train ML models on realistic elderly data to detect anomalies
- Apply ML to detect health risks in real-time  
- Build a live dashboard for caregivers to supervise residents and receive alerts

# 🧓 Smart Elderly Home Monitoring System

**A big data simulation project for real-time supervision of elderly residents using IoT, wearables, and machine learning.**
---


## Idea
- Simulate a connected elderly home: wearable + smart home sensor data
- Stream data in real time via Kafka
- Train ML models on realistic elderly data to detect anomalies
- Build a live dashboard for caregivers to supervise residents and receive alerts


## Potential Tech Stack Overview
| Component           | Tool/Tech               |
|---------------------|-------------------------|
| Data Simulation     | Python scripts          |
| Data Streaming      | Kafka                   |
| Processing Engine   | Spark Structured Streaming |
| Machine Learning    | Scikit-learn / PySpark MLlib |
| Storage             | PostgreSQL / Cassandra  |
| Dashboard           | Streamlit / Dash        |
| Containerization    | Docker                  |
## Data Streams

| Data Type       | Source         | Frequency     | Purpose                          |
|------------------|----------------|---------------|-----------------------------------|
| Heart rate        | Wearable       | 1/min         | Detect spikes/drops               |
| Motion sensor     | Smart home     | on event      | Inactivity detection              |
| Fridge usage      | Smart fridge   | on event      | Missed meals                      |
| Sleep quality     | Wearable       | 1/night       | Long-term trend analysis          |
| Medication intake | Simulated logs| on event      | Adherence issues                  |

## Machine Learning Alerts
- Detects:
  - Falls
  - Abnormal heart rate
  - No movement or food intake
  - Missed medication  
- Triggers real-time alerts

## Dashboard
- **Global View**: All residents, color-coded by status  
- **Resident View**: Timeline of health events + vitals  
- **Alerts Panel**: Real-time alerts with filtering  
---

## 🏁 Project Goals

- Build an end-to-end big data pipeline  
- Simulate realistic streaming data at scale  
- Apply ML to detect health risks in real-time  
- Visualize system output for real-world decision-making

---
