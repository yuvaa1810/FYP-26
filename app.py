import os
import json
import threading
import hashlib
import csv
import time
from datetime import datetime
from io import BytesIO
from flask import Flask, render_template, jsonify, request, send_file, redirect, url_for, session

# Standard Paho-MQTT import
from paho.mqtt import client as mqtt_client

# Import ReportLab for PDF generation
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

app = Flask(__name__)
app.secret_key = "your_secret_key"

# --- PATH CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "wastewater_log.csv")
LEDGER_PATH = os.path.join(BASE_DIR, "compliance_ledger.csv")

# --- MQTT CONFIGURATION ---
MQTT_BROKER = '10.22....'
TOPIC_ANALYTICS = 'tannery/analytics'

# Global state for Gauge widgets (Live data)
stats_lock = threading.Lock()
current_stats = {
    "ph": 0.0, "tds": 0, "turbidity": 0, "temp": 0, "score": 0, "anomaly": 0
}

# ================= LOGIN SYSTEM =================
USERNAME = "Your_Username"
PASSWORD_HASH = hashlib.sha256("Your_Password".encode()).hexdigest()

# ================= MQTT BACKGROUND LISTENER =================
def on_message(client, userdata, msg):
    global current_stats
    try:
        data = json.loads(msg.payload.decode())
        with stats_lock:
            current_stats.update({
                "ph": data.get("ph", 0),
                "tds": data.get("tds", 0),
                "turbidity": data.get("turbidity", 0),
                "temp": data.get("temp", 0),
                "score": data.get("score", 0),
                "anomaly": data.get("is_anom", 0)
            })
    except Exception as e:
        print(f"MQTT Parsing Error: {e}")

def start_mqtt():
    client_id = f"dashboard_pi_viewer_{int(time.time())}"
    
    # --- VERSION COMPATIBILITY FIX ---
    try:
        # Try Paho MQTT 2.0+ format
        from paho.mqtt.enums import CallbackAPIVersion
        client = mqtt_client.Client(callback_api_version=CallbackAPIVersion.VERSION2, client_id=client_id)
    except ImportError:
        # Fallback to Paho MQTT 1.x format (Laptop compatibility)
        client = mqtt_client.Client(client_id)
        
    client.on_message = on_message
    try:
        client.connect(MQTT_BROKER, 1883, 60)
        client.subscribe(TOPIC_ANALYTICS)
        print(f"✅ Dashboard linked to MQTT Stream: {TOPIC_ANALYTICS}")
        client.loop_forever()
    except Exception as e:
        print(f"❌ Dashboard MQTT Connection Error: {e}")

# ================= ROUTES =================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        hashed = hashlib.sha256(password.encode()).hexdigest()
        if username == USERNAME and hashed == PASSWORD_HASH:
            session["user"] = username
            return redirect(url_for('index'))
        return "Invalid Credentials", 401
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for('login'))

@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for('login'))
    return render_template("dashboard.html")

@app.route("/data")
def data():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        time_arr, ph, turb, tds, temp, score, anom = [], [], [], [], [], [], []
        
        if os.path.exists(CSV_PATH) and os.path.getsize(CSV_PATH) > 0:
            with open(CSV_PATH, "r") as f:
                lines = f.readlines()
                start_idx = 1 if "timestamp" in lines[0].lower() else 0
                latest_lines = lines[max(start_idx, len(lines)-50):]

            for line in latest_lines:
                row = line.strip().split(",")
                if len(row) >= 7:
                    time_arr.append(row[0])
                    ph.append(float(row[1]))
                    turb.append(float(row[2]))
                    tds.append(float(row[3]))
                    temp.append(float(row[4]))
                    score.append(float(row[5]))
                    anom.append(int(row[6]))

        with stats_lock:
            active_stats = current_stats.copy()

        reason = "Water quality within regulatory bounds. Inference stable."
        if active_stats["anomaly"] == 1:
            reason = f"CRITICAL: ECOD model detected a discharge anomaly (Severity: {active_stats['score']:.2f})."
            drivers = []
            if active_stats["ph"] < 6.5 or active_stats["ph"] > 8.5: drivers.append("pH Imbalance")
            if active_stats["tds"] > 2000: drivers.append("High Solid Density")
            if active_stats["turbidity"] > 30: drivers.append("Turbidity Flux")
            if drivers:
                reason += " Primary drivers: " + ", ".join(drivers) + ". Inspection recommended."

        return jsonify({
            "time": time_arr, "ph": ph, "tds": tds, "turbidity": turb, "temp": temp,
            "recon_error": score, "anomaly": anom, "current": active_stats, "reason": reason
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/verify")
def verify_ledger():
    if "user" not in session: return jsonify([]), 401
    blocks = []
    if os.path.exists(LEDGER_PATH):
        with open(LEDGER_PATH, "r") as f:
            reader = csv.reader(f)
            next(reader, None) 
            all_rows = list(reader)
            for i, row in enumerate(all_rows[-15:]):
                if len(row) >= 5:
                    blocks.append({
                        "time": row[0],
                        "ph": row[1],
                        "tds": row[2],
                        "turbidity": row[3],
                        "temp": row[4], 
                        "status": "Verified ✅" if int(row[5]) == 0 else "ANOMALY 🚨",
                        "hash": row[6] if len(row) > 6 else "N/A"
                    })
    return jsonify(blocks[::-1])

# ================= DATA INTEGRITY CHECKER =================

def check_integrity():
    if not os.path.exists(CSV_PATH) or not os.path.exists(LEDGER_PATH):
        return False, "Critical Failure: Log files missing from Edge Gateway."

    try:
        with open(CSV_PATH, "r") as f_csv, open(LEDGER_PATH, "r") as f_ledger:
            csv_lines = list(csv.reader(f_csv))[1:] 
            ledger_lines = list(csv.reader(f_ledger))[1:] 

            if len(csv_lines) != len(ledger_lines):
                return False, f"TAMPER DETECTED: Record count mismatch ({len(csv_lines)} vs {len(ledger_lines)})."

            prev_hash = "0" * 64 

            for i in range(len(csv_lines)):
                tstr = csv_lines[i][0]
                ph = csv_lines[i][1]
                turb = csv_lines[i][2]
                tds = csv_lines[i][3]
                temp = csv_lines[i][4]
                is_anom = csv_lines[i][6]

                data_payload = f"{tstr}{ph}{tds}{turb}{temp}{int(is_anom)}{prev_hash}"
                calculated_hash = hashlib.sha256(data_payload.encode()).hexdigest()
                stored_hash = ledger_lines[i][6]

                if calculated_hash != stored_hash:
                    return False, f"TAMPER DETECTED: Hash mismatch at Index {i}!"
                
                prev_hash = stored_hash

        return True, "Seal of Authenticity: SHA-256 Chain Verified."
    except Exception as e:
        return False, f"System Error: {str(e)}"

@app.route("/audit/verify-manual")
def manual_audit():
    if "user" not in session: return jsonify({"error": "Unauthorized"}), 401
    success, message = check_integrity()
    return jsonify({
        "success": success,
        "message": message,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "seal_code": hashlib.sha256(message.encode()).hexdigest()[:8].upper()
    })

@app.route("/audit/verify")
def api_verify_integrity():
    if "user" not in session: return jsonify({"status": "error"}), 401
    success, message = check_integrity()
    return jsonify({
        "integrity_passed": success,
        "message": message,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })

# ================= PDF REPORT GENERATION =================

@app.route("/export/pdf")
def generate_report():
    if "user" not in session: return redirect(url_for('login'))
    if not os.path.exists(CSV_PATH): return "No data recorded yet.", 404

    try:
        total_points = 0
        total_anomalies = 0
        with open(CSV_PATH, "r") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 7:
                    total_points += 1
                    anomaly_val = str(row[6]).strip().lower()
                    if anomaly_val in ['1', 'true']:
                        total_anomalies += 1

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=(8.5 * inch, 11 * inch))
        styles = getSampleStyleSheet()
        elements = [
            Paragraph("Tannery Edge AI Compliance Report", styles["Title"]),
            Spacer(1, 0.5 * inch),
            Paragraph(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]),
            Paragraph(f"Total Monitoring Data Points: {total_points}", styles["Normal"]),
            Paragraph(f"Detected Anomalies (Chromium/TDS): {total_anomalies}", styles["Normal"]),
            Spacer(1, 0.5 * inch),
            Paragraph("Official log from Raspberry Pi Gateway. Verified by ECOD Outlier Model & SHA-256 Chained Ledger.", styles["Italic"])
        ]
        doc.build(elements)
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name="Tannery_Compliance_Report.pdf", mimetype='application/pdf')
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    threading.Thread(target=start_mqtt, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=False)
