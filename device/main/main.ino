#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// WiFi
const char* WIFI_SSID = "Wifi_name";
const char* WIFI_PASSWORD = "Wifi_password";

// MQTT
const char* MQTT_BROKER = "broker.emqx.io";
const char* STUDENT_ID = "bm222mr";
const char* SENSOR_TOPIC = "lnu/iot/bm222mr/sensor";
const char* COMMAND_TOPIC = "lnu/iot/bm222mr/command/led";

// Pinnar
#define LED_PIN 27
#define DHT_PIN 14
#define DHT_TYPE DHT11

DHT dht(DHT_PIN, DHT_TYPE);
WiFiClient espClient;
PubSubClient client(espClient);

// Ta emot kommandon
void onMessage(char* topic, byte* payload, unsigned int length) {
  String msg = "";
  for (int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }
  StaticJsonDocument<64> doc;
  deserializeJson(doc, msg);
  bool state = doc["state"];
  digitalWrite(LED_PIN, state ? HIGH : LOW);
}

void connectWifi() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Ansluter till WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi ansluten! IP: " + WiFi.localIP().toString());
}

void connectMQTT() {
  while (!client.connected()) {
    Serial.print("Ansluter till MQTT...");
    if (client.connect("esp32_bm222mr")) {
      Serial.println("Ansluten!");
      client.subscribe(COMMAND_TOPIC);
    } else {
      Serial.print("Fel, rc=");
      Serial.println(client.state());
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  dht.begin();
  connectWifi();
  client.setServer(MQTT_BROKER, 1883);
  client.setCallback(onMessage);
  connectMQTT();
}

void loop() {
  if (!client.connected()) {
    connectMQTT();
  }
  client.loop();

  float temp = dht.readTemperature();
  Serial.print("Temperatur: ");
  Serial.println(temp);
  
  if (!isnan(temp)) {
    String payload = "{\"value\":" + String(temp) + ",\"timestamp\":0}";
    client.publish(SENSOR_TOPIC, payload.c_str());
    Serial.println("Skickade: " + payload);
  } else {
    Serial.println("Fel: kunde inte läsa sensor!");
  }
  delay(2000);
}