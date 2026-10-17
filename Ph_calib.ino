/*
 * pH Sensor Calibration Tool (Arduino Uno)
 * Use this to find the voltages for pH 7 (Tap Water) and pH 3 (Vinegar)
 */

const int potPin = A0; // pH sensor connected to Analog Pin 0

void setup() {
  Serial.begin(9600);
  Serial.println("--- pH Voltage Monitor ---");
  Serial.println("1. Dip probe in Tap Water (Neutral)");
  Serial.println("2. Dip probe in Vinegar (Acidic)");
}

void loop() {
  int rawValue = analogRead(potPin);
  
  // Calculate voltage (Arduino Uno is 10-bit: 0-1023)
  float voltage = rawValue * (5.0 / 1023.0);

  Serial.print("Raw ADC: ");
  Serial.print(rawValue);
  Serial.print(" | Voltage: ");
  Serial.println(voltage);
  
  delay(1000); // 1-second delay for stability
}