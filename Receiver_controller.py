import os
import time
import json
import joblib
import numpy as np
import csv 
import hashlib 
from paho.mqtt import client as mqtt_client

# Suppress Torch if it's lingering in the background
os.environ["PYOD_SKIP_TORCH"] = "1"

# ----- PATH CONFIGURATION -----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "wastewater_autoencoder.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "scaler.pkl")
LOG_PATH = os.path.join(BASE_DIR, "wastewater_log.csv")
COMPLIANCE_PATH = os.path.join(BASE_DIR, "compliance_ledger.csv")

# ----- NETWORK CONFIG -----
# CHANGE THIS: Use your laptop's IP (find it by typing 'ipconfig' in terminal)
MQTT_BROKER = '10.22.145.93' 
MQTT_PORT = 1883
TOPIC_TELEMETRY = 'tannery/sensor'
TOPIC_CONTROL = 'tannery/control'
CLIENT_ID = f'edge_laptop_{int(time.time())}'

# ----- Load model & scaler -----
model = None
scaler = None

try:
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    print(f"✅ REAL AI Loaded: ECOD Chromium-Detection model active.")
except Exception as e:
    print(f"🚨 Load Error: {e}")

def secure_ledger_log(tstr, ph, tds, turb, temp, is_anom):
    prev_hash = "0" * 64 
    if os.path.exists(COMPLIANCE_PATH):
        try:
            with open(COMPLIANCE_PATH, 'r') as f:
                lines = f.readlines()
                if len(lines) > 1:
                    prev_hash = lines[-1].split(",")[-1].strip()
        except: 
            pass

    data_payload = f"{tstr}{ph}{tds}{turb}{temp}{int(is_anom)}{prev_hash}"
    current_hash = hashlib.sha256(data_payload.encode()).hexdigest()

    file_exists = os.path.isfile(COMPLIANCE_PATH)
    with open(COMPLIANCE_PATH, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "ph", "tds", "turbidity", "temp", "status", "seal"])
        writer.writerow([tstr, ph, tds, turb, temp, int(is_anom), current_hash])

def log_data_lightweight(tstr, ph, turb, tds, temp, score, is_anom):
    file_exists = os.path.isfile(LOG_PATH)
    try:
        with open(LOG_PATH, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "ph", "turbidity", "tds", "temp", "score", "anomaly"])
            writer.writerow([tstr, ph, turb, tds, temp, f"{score:.4f}", int(is_anom)])
    except Exception as e:
        print(f"Logging error: {e}")

def process_telemetry(data, mqtt_client_obj=None):
    try:
        ph = float(data.get('ph', 7.0))
        turb = float(data.get('turbidity', 0))
        tds = float(data.get('tds', 0))
        temp = float(data.get('temperature', 25)) 
    except (ValueError, TypeError):
        print("Malformed telemetry data received.")
        return

    X = np.array([[ph, turb, tds, temp]], dtype=float)
    is_anom = False
    score = 0.0

    if model is not None and scaler is not None:
        try:
            Xs = scaler.transform(X)
            if hasattr(model, 'decision_function'):
                score = float(model.decision_function(Xs)[0])
                pred = model.predict(Xs)[0]
                is_anom = (int(pred) == 1)
        except Exception as e:
            print(f"Inference Error: {e}")
            is_anom = ph < 5.5 or ph > 9.5 or tds > 3000

    tstr = time.strftime("%Y-%m-%d %H:%M:%S")
    status_label = '🚨 ANOMALY' if is_anom else '✅ OK'
    print(f"[{tstr}] pH:{ph:.2f} | TDS:{tds:.0f} | Status:{status_label}")

    if mqtt_client_obj:
        mqtt_client_obj.publish(TOPIC_CONTROL, json.dumps({"divert": bool(is_anom)}))
        analytics_packet = {
            "score": round(score, 4),
            "is_anom": int(is_anom),
            "ph": ph, "tds": tds, "temp": temp, "turbidity": turb
        }
        mqtt_client_obj.publish("tannery/analytics", json.dumps(analytics_packet))

    log_data_lightweight(tstr, ph, turb, tds, temp, score, is_anom)
    secure_ledger_log(tstr, ph, tds, turb, temp, is_anom)

def mqtt_run():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"Connected to Local Broker: {MQTT_BROKER}")
            client.subscribe(TOPIC_TELEMETRY)
        else:
            print(f"Connection Failed. Code: {rc}")

    def on_message(client, userdata, msg):
        try:
            payload = msg.payload.decode()
            data = json.loads(payload)
            process_telemetry(data, mqtt_client_obj=client)
        except Exception as e:
            print(f"Message processing error: {e}")

    # --- UPDATED FOR COMPATIBILITY ---
    # Try the new versioning first, fallback to old style if it fails
    try:
        client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, CLIENT_ID)
    except AttributeError:
        client = mqtt_client.Client(CLIENT_ID)
    
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT)
        client.loop_forever()
    except Exception as e:
        print(f"MQTT Connection Error: {e}")

if __name__ == "__main__":
    print("--- Tannery Edge AI Gateway ---")
    mqtt_run()
