/* ESP32: Wastewater telemetry (simulate or real sensors) + MQTT control
 * GPIO: DIVERT_PIN toggles when anomaly is commanded (LED or relay)
 *
 * Setup:
 * - Put your WiFi SSID/PASS below, or set SIMULATE_MODE false and wire sensors.
 * - Use broker.hivemq.com for quick demo or your own broker.
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// === CONFIG ===
const bool SIMULATE_MODE = true;    // set false if you'll read actual sensors
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";

// MQTT broker (public for demo) or set to your local
const char* MQTT_BROKER = "broker.hivemq.com";
const int MQTT_PORT = 1883;
const char* TOPIC_TELEMETRY = "tannery/sensor";
const char* TOPIC_CONTROL = "tannery/control";

const int PUBLISH_INTERVAL_MS = 2000; // 2s

// Hardware
const int DIVERT_PIN = 2; // built-in LED on many ESP32 boards; use relay pin instead if you have relay
bool divertState = false;

WiFiClient espClient;
PubSubClient client(espClient);
unsigned long lastPublish = 0;
unsigned long seq = 0;

void callback(char* topic, byte* payload, unsigned int length) {
  // parse JSON payload
  StaticJsonDocument<200> doc;
  DeserializationError err = deserializeJson(doc, payload, length);
  if (err) {
    Serial.print("Invalid control message\n");
    return;
  }
  if (doc.containsKey("divert")) {
    bool v = doc["divert"];
    divertState = v;
    digitalWrite(DIVERT_PIN, divertState ? HIGH : LOW);
    Serial.printf("Control: set divert -> %s\n", divertState ? "ON" : "OFF");
  }
}

void connectMQTT() {
  while (!client.connected()) {
    Serial.print("Connecting MQTT...");
    if (client.connect("ESP32_Tannery_Demo")) {
      Serial.println("connected");
      client.subscribe(TOPIC_CONTROL);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 2s");
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(DIVERT_PIN, OUTPUT);
  digitalWrite(DIVERT_PIN, LOW);

  // connect Wi-Fi
  Serial.printf("Connecting to WiFi %s\n", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  int wi = 0;
  while (WiFi.status() != WL_CONNECTED && wi < 20) {
    delay(500);
    Serial.print(".");
    wi++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected.");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi failed. Proceeding without WiFi (Serial only).");
  }

  client.setServer(MQTT_BROKER, MQTT_PORT);
  client.setCallback(callback);
}

float randNormal(float mu, float sigma) {
  // Box-Muller
  float u1 = random(1, 10000) / 10000.0;
  float u2 = random(1, 10000) / 10000.0;
  float z0 = sqrt(-2.0 * log(u1)) * cos(2*PI*u2);
  return z0 * sigma + mu;
}

void publishTelemetry(float ph, float turb, float cond, float orp, float temp, float flow) {
  // JSON
  StaticJsonDocument<256> doc;
  doc["seq"] = seq++;
  doc["ph"] = ph;
  doc["turbidity"] = turb;
  doc["conductivity"] = cond;
  doc["orp"] = orp;
  doc["temp"] = temp;
  doc["flow"] = flow;
  doc["divert_state"] = divertState;
  char buffer[256];
  size_t n = serializeJson(doc, buffer);
  // Serial CSV line for direct serial reading (timestamp,ph,cond,turb,orp,temp,flow)
  Serial.printf("%lu,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f\n", millis(), ph, turb, cond, orp, temp, flow);

  // publish MQTT if connected
  if (WiFi.status() == WL_CONNECTED) {
    if (!client.connected()) connectMQTT();
    client.publish(TOPIC_TELEMETRY, buffer, n);
  }
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    client.loop();
  } else {
    // still allow serial-based control if needed
  }

  if (millis() - lastPublish > PUBLISH_INTERVAL_MS) {
    lastPublish = millis();
    float ph, turb, cond, orp, temp, flow;

    if (SIMULATE_MODE) {
      // Normal baseline most of the time, occasional anomalies
      bool anomalyNow = (random(0, 100) < 8); // 8% chance to simulate anomaly spike
      if (!anomalyNow) {
        ph = randNormal(7.0, 0.15);
        turb = randNormal(80, 4);
        cond = randNormal(400, 25);
        orp = randNormal(300, 10);
        temp = randNormal(28, 1);
        flow = randNormal(1.5, 0.05);
      } else {
        // anomaly - chromium-like spike (low pH, high conductivity & turbidity)
        ph = randNormal(4.5, 0.2);
        turb = randNormal(250, 20);
        cond = randNormal(1200, 80);
        orp = randNormal(150, 20);
        temp = randNormal(29, 1);
        flow = randNormal(1.6, 0.08);
      }
    } else {
      // TODO: plug actual sensors here
      // Example: read analog pins (remember to use ADC scaling, stable op-amp, sensor conditioning)
      ph = analogRead(34) / 4095.0 * 14.0;      // placeholder
      cond = analogRead(35);                    // placeholder
      turb = analogRead(32);                    // placeholder
      orp = analogRead(33);                     // placeholder
      temp = 25.0;
      flow = 1.5;
    }

    publishTelemetry(ph, turb, cond, orp, temp, flow);
  }
}
