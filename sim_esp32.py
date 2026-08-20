import paho.mqtt.client as mqtt
import json
import time
import random
import msvcrt # Allows keyboard input without hitting Enter

# --- CONFIGURATION ---
MQTT_BROKER = "10.22.145.93" 
TOPIC = "tannery/sensor"

client = mqtt.Client("Simulated_ESP32")
client.connect(MQTT_BROKER, 1883)

# Simulation State
anomaly_mode = False

print("🚀 Chrome-Effluent Simulator Active.")
print("-" * 40)
print("COMMANDS:")
print("Press 'A' -> Trigger CHROME LIQUOR anomaly")
print("Press 'N' -> Return to NORMAL process water")
print("Press Ctrl+C -> Stop simulation")
print("-" * 40)

try:
    while True:
        # 1. Handle Keyboard Input
        if msvcrt.kbhit():
            key = msvcrt.getch().decode('utf-8').lower()
            if key == 'a':
                anomaly_mode = True
                print("\n[EVENT] 🚨 CHROME DISCHARGE TRIGGERED!")
            elif key == 'n':
                anomaly_mode = False
                print("\n[EVENT] ✅ SWITCHED TO NORMAL WASH WATER")

        # 2. Generate Data based on your Training Stats
        if not anomaly_mode:
            # Matches your Training: ph ~ 7.8, tds ~ 1200, turb ~ 30, temp ~ 27
            ph = random.normalvariate(7.8, 0.2)
            turb = random.normalvariate(30, 5)
            tds = random.normalvariate(1200, 100)
            temp = random.normalvariate(27, 1)
        else:
            # Matches your Training: ph ~ 3.8, tds ~ 15000, turb ~ 250, temp ~ 45
            ph = random.normalvariate(3.8, 0.3)
            turb = random.normalvariate(250, 40)
            tds = random.normalvariate(15000, 1500)
            temp = random.normalvariate(45, 3)

        # 3. Format and Publish
        data = {
            "ph": round(ph, 2),
            "turbidity": round(turb, 2),
            "tds": round(tds, 2),
            "temperature": round(temp, 2)
        }

        payload = json.dumps(data)
        client.publish(TOPIC, payload)
        
        # Using \r keeps the terminal clean by overwriting the same line
        status = "🚨 ANOMALY" if anomaly_mode else "🟢 NORMAL "
        print(f"📡 {status} | Sending: {payload}", end='\r')
        
        time.sleep(2) # Faster updates for a snappier demo

except KeyboardInterrupt:
    print("\n\nStopping Simulation...")
    client.disconnect()