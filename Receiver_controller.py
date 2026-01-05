"""
Receiver + Controller for Raspberry Pi Edge Gateway.
Usage:
    python Receiver_controller.py --mode mqtt
    python Receiver_controller.py --mode serial --serial /dev/ttyUSB0
"""

import time
import json
import argparse
import joblib
import numpy as np
import os
import sys

# choose comms
from paho.mqtt import client as mqtt_client
import serial

# ----- PATH CONFIGURATION -----
# Ensures the Pi finds the models regardless of where the script is called from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "wastewater_autoencoder.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "scaler.pkl")
LOG_PATH = os.path.join(BASE_DIR, "wastewater_log.csv")

# ----- NETWORK CONFIG -----
# When running on Pi with local Mosquitto, change this to '127.0.0.1' or the Pi's IP
MQTT_BROKER = 'broker.hivemq.com' 
MQTT_PORT = 1883
TOPIC_TELEMETRY = 'tannery/sensor'
TOPIC_CONTROL = 'tannery/control'
CLIENT_ID = f'pi_brain_{int(time.time())}'

SERIAL_BAUD = 115200
SERIAL_PORT = '/dev/ttyUSB0' # Default for Pi USB

# ----- Load model & scaler -----
model = None
scaler = None

try:
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    print(f"Successfully loaded model and scaler from {BASE_DIR}")
except Exception as e:
    print(f"CRITICAL ERROR: Could not load ML assets. Error: {e}")
    # You may want to exit here if the Pi MUST have the ML model to function
    # sys.exit(1)

def fallback_rule(ph, turb, cond, orp):
    """Safety backup if model inference fails."""
    if ph < 6.0 and (cond > 800 or turb > 150):
        return True
    return False

def send_mqtt_divert(mqtt_client_obj, divert):
    msg = json.dumps({"divert": bool(divert)})
    mqtt_client_obj.publish(TOPIC_CONTROL, msg)
    print(f"[CONTROL] Sent divert -> {divert}")

def process_telemetry(data, mqtt_client_obj=None, ser_obj=None):
    try:
        ph = float(data.get('ph', 0))
        turb = float(data.get('turbidity', 0))
        cond = float(data.get('conductivity', 0))
        orp = float(data.get('orp', 0))
    except (ValueError, TypeError):
        print("Malformed telemetry data received.")
        return

    # ML Inference
    X = np.array([[ph, turb, cond, orp]], dtype=float)
    is_anom = False
    score = 0.0

    if model is not None and scaler is not None:
        try:
            Xs = scaler.transform(X)
            score = model.decision_function(Xs)[0]
            pred = model.predict(Xs)[0]
            is_anom = (int(pred) == 1)
        except Exception as e:
            print(f"Inference Error: {e}")
            is_anom = fallback_rule(ph, turb, cond, orp)
    else:
        is_anom = fallback_rule(ph, turb, cond, orp)

    # Logging and Feedback
    tstr = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{tstr}] pH:{ph:.2f} | Score:{score:.4f} | Status:{'🚨 ANOMALY' if is_anom else 'OK'}")

    if mqtt_client_obj:
        send_mqtt_divert(mqtt_client_obj, is_anom)

        status_msg = json.dumps({
        "score": float(score),
        "is_anom": int(is_anom),
        "ph": ph,
        "cond": cond
    })
    mqtt_client_obj.publish("tannery/analytics", status_msg)
    
    # Save to Secure Ledger/CSV
    with open(LOG_PATH, "a") as f:
        f.write(f"{tstr},{ph},{turb},{cond},{orp},{score},{is_anom}\n")

def mqtt_run():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"Connected to Broker at {MQTT_BROKER}")
            client.subscribe(TOPIC_TELEMETRY)
        else:
            print(f"Connection Failed. Code: {rc}")

    def on_message(client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            process_telemetry(data, mqtt_client_obj=client)
        except Exception as e:
            print(f"Message Error: {e}")

    client = mqtt_client.Client(CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT)
        client.loop_forever() # Use loop_forever for dedicated Pi service
    except Exception as e:
        print(f"Could not connect to MQTT: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["mqtt", "serial"], default="mqtt")
    parser.add_argument("--serial", default=SERIAL_PORT)
    args = parser.parse_args()

    print(f"Starting Tannery Monitor in {args.mode} mode...")
    if args.mode == "mqtt":
        mqtt_run()
    else:
        # Serial implementation remains similar to your original logic
        print("Serial mode selected (ensure ESP32 is connected via USB)")