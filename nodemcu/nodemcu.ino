#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <WiFiUdp.h>

// =====================================================
// WIFI
// =====================================================

const char* ssid = "NOME_RETE";
const char* password = "PASSWORD_RETE";

// =====================================================
// SERVER
// =====================================================

ESP8266WebServer server(80);
WiFiUDP udp;

const unsigned int DISCOVERY_PORT = 4210;
const int LED_PIN = LED_BUILTIN;

// =====================================================
// LAMPEGGIO
// =====================================================

void blinkLED(int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, LOW);
    delay(200);

    digitalWrite(LED_PIN, HIGH);
    delay(200);

    delay(150);
  }
}

// =====================================================
// HTTP
// =====================================================

void handleRequest() {

  String path = server.uri();

  Serial.print("HTTP: ");
  Serial.println(path);

  if (path.length() == 2) {

    char command = path.charAt(1);

    if (command >= 'A' && command <= 'Z') {

      int times = command - 'A' + 1;

      Serial.print("Comando ");
      Serial.print(command);
      Serial.print(" -> ");
      Serial.print(times);
      Serial.println(" lampeggi");

      blinkLED(times);

      server.send(
        200,
        "text/plain",
        String("OK: ") + command
      );

      return;
    }
  }

  server.send(
    200,
    "text/plain",
    "ESP8266 OK - usa /A /B /C /D ..."
  );
}

// =====================================================
// DISCOVERY UDP
// =====================================================

void handleDiscovery() {

  int packetSize = udp.parsePacket();

  if (!packetSize) {
    return;
  }

  char buffer[64];

  int len = udp.read(buffer, sizeof(buffer) - 1);

  if (len <= 0) {
    return;
  }

  buffer[len] = '\0';

  Serial.print("UDP: ");
  Serial.println(buffer);

  if (strcmp(buffer, "NOOKAI_DISCOVER") == 0) {

    String response = "NOOKAI_ESP8266 ";

    response += WiFi.localIP().toString();

    udp.beginPacket(udp.remoteIP(), udp.remotePort());
    udp.write(response.c_str());
    udp.endPacket();

    Serial.print("Discovery response: ");
    Serial.println(response);
  }
}

// =====================================================
// SETUP
// =====================================================

void setup() {

  Serial.begin(115200);
  delay(500);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);

  Serial.println();
  Serial.println("==============================");
  Serial.println("NOOKAI ESP8266");
  Serial.println("==============================");

  // DHCP: nessun IP statico

  WiFi.mode(WIFI_STA);

  Serial.print("Connessione a: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("Wi-Fi CONNESSO");

  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  Serial.print("Gateway: ");
  Serial.println(WiFi.gatewayIP());

  // ===================================================
  // HTTP SERVER
  // ===================================================

  server.on("/", handleRequest);
  server.onNotFound(handleRequest);

  server.begin();

  // ===================================================
  // UDP DISCOVERY
  // ===================================================

  udp.begin(DISCOVERY_PORT);

  Serial.print("Discovery UDP porta: ");
  Serial.println(DISCOVERY_PORT);

  Serial.println("==============================");
  Serial.println("PRONTO");
  Serial.println("==============================");

  // 1 lampeggio = pronto
  blinkLED(1);
}

// =====================================================
// LOOP
// =====================================================

void loop() {

  server.handleClient();

  handleDiscovery();
}