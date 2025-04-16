#include <Wire.h>
#include <Adafruit_INA219.h>
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <TimeLib.h>  // Keep TimeLib
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <ArduinoJson.h> // Include ArduinoJson

Adafruit_INA219 ina219;
Adafruit_MPU6050 mpu;

const char* ssid = "your Wi-Fi SSID"; // Replace with your Wi-Fi SSID
const char* password = "your Wi-Fi password"; // Replace with your Wi-Fi password

ESP8266WebServer server(80);

// Define custom I2C pins
#define SDA_PIN D3  // GPIO0
#define SCL_PIN D4  // GPIO2

// Define a fixed epoch time (seconds since Jan 1, 1970)
// MUST BE UPDATED MANUALLY
#define FIXED_EPOCH_TIME 1678886400 // March 15, 2023 00:00:00 GMT - Replace with a current timestamp

void setup() {
  Serial.begin(115200);
  Serial.println("Starting Setup...");

  // Initialize I2C with custom pins
  Serial.println("Initializing I2C with custom pins...");
  Wire.begin(SDA_PIN, SCL_PIN);  // Initialize I2C with custom pins
  Serial.print("SDA_PIN = "); Serial.println(SDA_PIN);
  Serial.print("SCL_PIN = "); Serial.println(SCL_PIN);
  Serial.println("I2C Initialized with custom pins.");

  // Scan I2C bus for devices
  Serial.println("Scanning I2C bus...");
  byte count = 0;
  for (byte i = 8; i < 120; i++)
  {
    Wire.beginTransmission (i);
    if (Wire.endTransmission () == 0)
    {
      Serial.print ("Found I2C device at address 0x");
      if (i < 16) Serial.print ("0");
      Serial.print (i, HEX);
      Serial.println ("  !");
      count++;
    }
  }
  Serial.print ("Found ");
  Serial.print (count, DEC);
  Serial.println (" device(s).");

  // Initialize INA219
  Serial.println("Initializing INA219...");
  // Give the INA219 a chance to start
  delay(100);
  if (!ina219.begin()) {
    Serial.println("Failed to find INA219 chip");
    while (1) { delay(10); }
  }
  Serial.println("INA219 Initialized.");

  // Initialize MPU6050
  Serial.println("Initializing MPU6050...");
  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) { delay(10); }
  }
  Serial.println("MPU6050 Found");
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  Serial.println("MPU6050 Initialized with settings.");

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();

  Serial.print("Connected to WiFi. IP address: ");
  Serial.println(WiFi.localIP());

  // Initialize Time
  Serial.println("Initializing Time from fixed value...");
  setTime(FIXED_EPOCH_TIME); // Set system time to the fixed epoch time
  Serial.println("System time set.");

  server.on("/", handleRoot);
  server.begin();
  Serial.println("Web server started!");
}

void loop() {
  server.handleClient();
  // Do NOT update the time in the loop, as there is no NTP
}

void handleRoot() {
  // 1. Get Sensor Data
  float busVoltage_V = ina219.getBusVoltage_V();
  float shuntVoltage_mV = ina219.getShuntVoltage_mV();
  float current_mA = ina219.getCurrent_mA();
  float power_mW = ina219.getPower_mW();
  float loadVoltage_V = busVoltage_V + (shuntVoltage_mV / 1000.0); // Calculate load voltage

  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  // 2. Prepare JSON Document
  StaticJsonDocument<256> doc; // Adjust size as needed
  doc["time"] = hour() * 3600L + minute() * 60 + second(); // Seconds since midnight

  JsonObject ina219Data = doc.createNestedObject("ina219");
  ina219Data["busV"] = round(busVoltage_V * 1000) / 1000.0; // 3 decimal places
  ina219Data["shuntV"] = round(shuntVoltage_mV * 1000) / 1000.0;
  ina219Data["curr"] = round(current_mA * 1000) / 1000.0;
  ina219Data["power"] = round(power_mW * 1000) / 1000.0;
  ina219Data["loadV"] = round(loadVoltage_V * 1000) / 1000.0;

  JsonObject mpu6050Data = doc.createNestedObject("mpu6050");
  mpu6050Data["accX"] = round(a.acceleration.x * 100) / 100.0; // 2 decimal places
  mpu6050Data["accY"] = round(a.acceleration.y * 100) / 100.0;
  mpu6050Data["accZ"] = round(a.acceleration.z * 100) / 100.0;
  mpu6050Data["gyroX"] = round(g.gyro.x * 100) / 100.0;
  mpu6050Data["gyroY"] = round(g.gyro.y * 100) / 100.0;
  mpu6050Data["gyroZ"] = round(g.gyro.z * 100) / 100.0;
  mpu6050Data["temp"] = round(temp.temperature * 100) / 100.0;

  // 3. Serialize JSON to String
  String jsonString;
  serializeJson(doc, jsonString);

  // 4. Send Data
  server.send(200, "application/json", jsonString);

  // (Optional) Print JSON to Serial for debugging
  Serial.println(jsonString);
}
