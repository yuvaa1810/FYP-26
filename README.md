# Edge-IIoT for Smart Tannery Effluent Monitoring with Chromium Surrogates and Secure Compliance Ledger

An affordable, edge-based industrial wastewater monitoring and control system designed for real-time detection of chromium-related anomalies in tannery effluents.

The system combines **IoT sensing, Edge AI, anomaly detection, automated control, and cryptographically secured compliance logging** into a single decentralized architecture.

---

## 📌 Project Overview

The leather tanning industry generates wastewater containing potentially hazardous chemical contaminants, including chromium compounds. Conventional industrial monitoring systems can provide accurate chemical analysis, but their high cost and infrastructure requirements make continuous monitoring difficult for small and medium-scale tanneries.

This project proposes an **Edge-IIoT based monitoring and control system** that uses low-cost water-quality sensors as surrogate indicators of chromium discharge.

Instead of relying on expensive dedicated heavy-metal analyzers, the system analyzes the combined behavior of:

* pH
* Total Dissolved Solids (TDS)
* Turbidity
* Temperature

These parameters are transmitted from an **ESP32 sensing node** to a **Raspberry Pi 4 edge gateway**, where the ECOD anomaly detection model performs local inference.

When an anomalous discharge is detected, the system automatically activates a solenoid valve to divert the contaminated effluent. Sensor readings, anomaly events, and control actions are also recorded in a **SHA-256 hash-chained secure compliance ledger**.

A web dashboard provides real-time visibility into sensor readings, anomaly events, system status, and ledger integrity.

---

## 🏗️ System Architecture

```text
┌──────────────────────────────┐
│       Water / Effluent       │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│        ESP32 Sensor Node     │
│                              │
│  • pH Sensor                 │
│  • TDS Sensor                │
│  • Turbidity Sensor          │
│  • Temperature Sensor        │
└──────────────┬───────────────┘
               │
               │ MQTT / JSON
               ▼
┌──────────────────────────────┐
│     Raspberry Pi 4 Edge      │
│          Gateway             │
│                              │
│  • MQTT Broker               │
│  • ECOD Anomaly Detection    │
│  • Data Processing           │
│  • Secure Compliance Ledger  │
│  • Flask Backend             │
└──────────────┬───────────────┘
               │
        ┌──────┴─────────┐
        ▼                ▼
┌───────────────┐  ┌────────────────┐
│ Solenoid Valve│  │ Web Dashboard  │
│ / Relay       │  │                │
│               │  │ • Sensor Data  │
│ Automated     │  │ • Alerts       │
│ Diversion     │  │ • Anomaly Score│
└───────────────┘  │ • Secure Ledger│
                   └────────────────┘
```

---

## ⚙️ Key Features

### 🔬 Surrogate Sensing

The system uses low-cost sensors to identify the multivariate signature associated with chromium tanning discharge.

The monitored parameters are:

| Parameter   | Purpose                                                               |
| ----------- | --------------------------------------------------------------------- |
| pH          | Detects acidic changes associated with tanning liquor                 |
| TDS         | Detects significant increases in dissolved salts and chemical content |
| Turbidity   | Indicates suspended particles and changes in effluent composition     |
| Temperature | Provides additional contextual information for anomaly detection      |

Rather than relying on a single fixed threshold, the system uses **multi-parameter sensor fusion** to identify abnormal combinations of sensor readings.

---

### 🧠 Edge-Based Anomaly Detection

The system uses **ECOD (Empirical Cumulative Distribution Functions for Outlier Detection)** for unsupervised anomaly detection.

The model analyzes the distribution of the sensor features and assigns an anomaly score based on tail probabilities.

The model operates directly on the Raspberry Pi, allowing inference to be performed locally without requiring continuous cloud connectivity.

The training pipeline uses:

* Python
* PyOD
* MinMaxScaler
* Joblib
* Synthetic industrial sensor data

The trained model and scaler are serialized and deployed to the Raspberry Pi for real-time inference.

---

### 📡 MQTT Communication

Sensor data is transmitted from the ESP32 to the Raspberry Pi using the **MQTT publish-subscribe protocol**.

Sensor readings are formatted as JSON before being processed by the edge gateway.

The main receiver and control logic is implemented in:

```text
receiver_controller.py
```

---

### 🚨 Automated Anomaly Response

When the ECOD anomaly score exceeds the configured decision threshold:

1. The Raspberry Pi identifies the event as anomalous.
2. A control signal is generated.
3. The relay module is activated.
4. The solenoid valve is triggered.
5. The contaminated effluent is diverted.
6. The event is recorded in the secure ledger.
7. The dashboard displays the anomaly and control response.

The experimental implementation achieved an end-to-end response time of **less than 2 seconds** from sensor acquisition to valve activation.

---

### 🔐 SHA-256 Secure Compliance Ledger

To protect the integrity of environmental monitoring records, the system implements a lightweight hash-chained compliance ledger.

Each ledger entry contains:

* Timestamp
* Sensor readings
* Machine-learning output
* Previous block hash
* Current block hash

The current hash is generated using SHA-256 and incorporates the previous record's hash.

```text
Block 1
   │
   ▼
Block 2
   │
   ▼
Block 3
   │
   ▼
Block 4
```

If a historical record is modified, its hash changes and breaks the chain relationship with subsequent records.

The implementation uses Python's `hashlib` library and a JSON-based append-only ledger.

---

## 🖥️ Web Dashboard

The monitoring interface provides three major functions:

### Sensor Monitoring

Displays real-time:

* pH
* TDS
* Turbidity
* Temperature
* Sensor trends

### Anomaly Monitoring

Displays:

* Anomaly status
* Triggering sensor values
* ECOD anomaly score
* Timestamp
* Solenoid valve response

### Compliance Ledger

Provides a read-only view of the SHA-256 hash-chained records, allowing the integrity of monitoring events to be verified from the dashboard.

---

## 🧰 Hardware

| Component              | Role                               |
| ---------------------- | ---------------------------------- |
| Raspberry Pi 4 Model B | Edge gateway and local processing  |
| ESP32                  | Sensor acquisition and control     |
| pH Sensor              | pH measurement                     |
| TDS Sensor             | Total dissolved solids measurement |
| Turbidity Sensor       | Turbidity measurement              |
| DS18B20                | Temperature measurement            |
| Relay Module           | Solenoid control                   |
| 12V DC Solenoid Valve  | Automated effluent diversion       |

---

## 💻 Software & Technologies

**Programming**

* Python
* Embedded C / Arduino

**Machine Learning**

* PyOD
* ECOD
* Scikit-learn preprocessing
* Joblib

**IoT & Communication**

* ESP32
* Raspberry Pi
* MQTT
* JSON
* Mosquitto

**Web Application**

* Flask
* React
* HTML
* CSS
* REST API

**Security**

* SHA-256
* Hash-chained audit logging

---

## 📊 Experimental Results

The anomaly detection system was evaluated using a dataset containing **5,500 samples**, including normal operating conditions and simulated chromium leak events.

| Metric    | Normal | Chrome Leak |
| --------- | -----: | ----------: |
| Precision |   1.00 |        0.65 |
| Recall    |   0.95 |        1.00 |
| F1-score  |   0.97 |        0.79 |
| Support   |   5000 |         500 |

Overall accuracy was approximately **95.1%**, while recall for the simulated chromium-leak class reached **100%**.

The system was intentionally configured toward high sensitivity so that potentially hazardous discharge events were not missed.

The experimental implementation also demonstrated:

* **< 2 second** end-to-end anomaly response
* Successful automated solenoid actuation
* Successful SHA-256 ledger integrity verification
* Real-time dashboard monitoring
* Local edge inference without dependence on cloud infrastructure

---

## 💰 Cost Advantage

The proposed prototype was designed as a low-cost alternative to conventional industrial effluent analyzers.

| Feature        | Proposed System                 | Industrial Analyzer         |
| -------------- | ------------------------------- | --------------------------- |
| Core Hardware  | ESP32 + Raspberry Pi 4          | Industrial PLC / Controller |
| Sensing        | Multi-sensor surrogate approach | Direct chemical analysis    |
| Data Integrity | SHA-256 secure ledger           | Standard data logging       |
| Communication  | MQTT                            | Proprietary protocols       |
| Approx. Cost   | ₹8,000–₹12,000                  | ₹2,00,000–₹5,00,000         |

The report estimates a substantial reduction in implementation cost while retaining real-time anomaly detection and secure audit logging.

---

## 📁 Repository Structure

```text
FYP-26/
│
├── data/
│   └── Project datasets and supporting data
│
├── screenshots/
│   └── Dashboard and system screenshots
│
├── templates/
│   └── Dashboard templates
│
├── app.py
├── receiver_controller.py
├── broker_start.py
├── sim_esp32.py
├── requirements.txt
│
├── scaler.pkl
├── wastewater_autoencoder.pkl
│
└── README.md
```

> **Note:** Model files and generated datasets may be reorganized as the project repository is cleaned and documented.

---

## 📸 Project Demonstration

### Hardware Setup

*Add hardware prototype photograph here.*

### System Architecture

*Add system architecture diagram here.*

### Dashboard

*Add dashboard screenshots here.*

### Anomaly Detection

*Add confusion matrix / anomaly detection results here.*

### Secure Compliance Ledger

*Add SHA-256 ledger screenshot here.*

---

## 📄 Documentation

The complete final-year project report is included in this repository.

The report covers:

* System architecture
* Hardware implementation
* Surrogate sensing methodology
* ECOD anomaly detection
* Model training and deployment
* MQTT communication
* Automated control
* SHA-256 secure ledger
* Dashboard implementation
* Experimental results
* Hardware setup
* Cost analysis
* Future work

---

## 🚀 Future Work

Potential extensions include:

* Integration of additional water-quality parameters
* Deployment across multiple tannery monitoring nodes
* Improved field calibration and long-term sensor validation
* Integration with municipal wastewater treatment infrastructure
* Secure remote communication
* Expanded compliance reporting
* Larger real-world industrial datasets
* Hardware miniaturization and dedicated PCB development

---

## 👥 Project Team

**Yuvashree S**
**Rishit Rodriquez J S**
**Thejashiwini M**

Department of Electronics and Communication Engineering
Rajalakshmi Institute of Technology, Chennai

---

## 📜 Project

**Edge-IIoT for Smart Tannery Effluent Monitoring with Chromium Surrogates and Secure Compliance Ledger**

Final Year Project — B.E. Electronics and Communication Engineering

---
