/*
  Demo firmware sketch for ESP32 + RC522.
  Reads RFID UID and posts to backend API.
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN 5
#define RST_PIN 22

MFRC522 rfid(SS_PIN, RST_PIN);

const char* ssid = "YOUR_WIFI";
const char* password = "YOUR_PASSWORD";
const char* apiUrl = "http://YOUR_SERVER_IP:8000/api/scan";
const char* deviceId = "LIB_GATE_1";

void setup() {
  Serial.begin(115200);
  SPI.begin();
  rfid.PCD_Init();

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");
}

String uidToString(MFRC522::Uid* uid) {
  String out = "";
  for (byte i = 0; i < uid->size; i++) {
    if (uid->uidByte[i] < 0x10) out += "0";
    out += String(uid->uidByte[i], HEX);
  }
  out.toUpperCase();
  return out;
}

void loop() {
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    delay(100);
    return;
  }

  String uid = uidToString(&rfid.uid);
  Serial.println("Scanned UID: " + uid);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(apiUrl);
    http.addHeader("Content-Type", "application/json");

    String payload = "{\"rfid_uid\":\"" + uid + "\",\"device_id\":\"" + deviceId + "\"}";
    int code = http.POST(payload);
    String body = http.getString();

    Serial.printf("HTTP %d: %s\n", code, body.c_str());
    http.end();
  }

  rfid.PICC_HaltA();
  delay(1200);
}
