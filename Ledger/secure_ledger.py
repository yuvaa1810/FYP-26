import hashlib
import time
import os
import json
from paho.mqtt import client as mqtt_client

# ----- CONFIGURATION -----
LEDGER_FILE = os.path.join(os.path.dirname(__file__), "compliance_ledger.csv")
MQTT_BROKER = "127.0.0.1" # Change to 'broker.hivemq.com' if testing without local Mosquitto
TOPIC_STORAGE = "tannery/secure_log"

def get_last_hash():
    """Reads the last hash to link the new block (Blockchain logic)."""
    if not os.path.exists(LEDGER_FILE):
        return "0" * 64  # Genesis Hash
    
    with open(LEDGER_FILE, "r") as f:
        lines = f.readlines()
        if len(lines) <= 1: 
            return "0" * 64
        last_line = lines[-1].strip()
        return last_line.split(",")[-1] # Hash is the last column

def write_block(data_json):
    """Creates a hashed entry (block) in the ledger."""
    prev_hash = get_last_hash()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Extract updated sensor values
    ph = data_json.get('ph', 0)
    tds = data_json.get('tds', 0)
    temp = data_json.get('temp', 0)
    score = data_json.get('score', 0)
    anom = data_json.get('is_anom', 0)
    
    # The Cryptographic Seal: Hash (Previous Hash + Current Data)
    # This links this entry to the one before it.
    data_content = f"{timestamp}|{ph}|{tds}|{temp}|{score}|{anom}"
    block_hash = hashlib.sha256((prev_hash + data_content).encode()).hexdigest()
    
    # Save to CSV
    file_exists = os.path.exists(LEDGER_FILE)
    with open(LEDGER_FILE, "a") as f:
        if not file_exists:
            # Updated Header
            f.write("Timestamp,pH,TDS,Temp,Score,Anomaly,PrevHash,CurrentHash\n")
        
        entry = f"{timestamp},{ph},{tds},{temp},{score},{anom},{prev_hash},{block_hash}\n"
        f.write(entry)
    
    print(f"🔒 Ledger Sealed: {block_hash[:10]}... (Linked to {prev_hash[:10]}...)")

# ----- MQTT Listener -----
def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        write_block(data)
    except Exception as e:
        print(f"Ledger Error: {e}")

if __name__ == "__main__":
    print("📜 Compliance Ledger Service Started...")
    client = mqtt_client.Client("Ledger_Service")
    client.on_message = on_message
    
    # If you're testing at college without a local broker, use 'broker.hivemq.com'
    try:
        client.connect(MQTT_BROKER, 1883)
        client.subscribe(TOPIC_STORAGE)
        client.loop_forever()
    except Exception as e:
        print(f"Connection Error: {e}. Is Mosquitto running on the Pi?")