#include <WiFi.h>
#include <Firebase_ESP_Client.h>

// ================= WIFI =================
#define WIFI_SSID "Redmi 12 5G"
#define WIFI_PASSWORD "12345678"

// =============== FIREBASE ===============
#define API_KEY "AIzaSyCfCRcfTkFUjlAl5lkb39KYjstShwUZiwE"
#define DATABASE_URL "https://face-recognition-securit-5dd85-default-rtdb.firebaseio.com"

// Firebase objects
FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig config;

// ============== PIN SETUP ==============
#define RELAY_PIN 26
#define GREEN_LED 14
#define RED_LED 27
#define BUZZER 25

bool doorOpen = false;

void setup() {
  Serial.begin(115200);

  pinMode(RELAY_PIN, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  pinMode(BUZZER, OUTPUT);

  digitalWrite(RELAY_PIN, HIGH);   // Relay OFF
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, HIGH);     // Red ON initially
  digitalWrite(BUZZER, LOW);

  // WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }
  Serial.println("\nConnected to WiFi");

  // Firebase setup
  config.api_key = API_KEY;
  config.database_url = DATABASE_URL;

  // Anonymous sign-up (needed even with public rules)
  if (Firebase.signUp(&config, &auth, "", "")) {
    Serial.println("SignUp OK");
  } else {
    Serial.printf("SignUp failed: %s\n", config.signer.signupError.message.c_str());
  }

  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);

  Serial.println(Firebase.ready() ? "Firebase connected" : "Firebase not ready");
}

void unlockDoor() {
  Serial.println("Door UNLOCKED");
  digitalWrite(RELAY_PIN, LOW);
  digitalWrite(GREEN_LED, HIGH);
  digitalWrite(RED_LED, LOW);

  digitalWrite(BUZZER, HIGH);
  delay(600);
  digitalWrite(BUZZER, LOW);

  doorOpen = true;
  delay(5000);
  lockDoor();
}

void lockDoor() {
  Serial.println("Door LOCKED");
  digitalWrite(RELAY_PIN, HIGH);
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, HIGH);

  doorOpen = false;

  Firebase.RTDB.setString(&fbdo, "/door_lock/access", "No");
  Firebase.RTDB.setString(&fbdo, "/door_lock/command", "LOCK");
}

void loop() {
  if (Firebase.RTDB.getString(&fbdo, "/door_lock/command")) {
    String command = fbdo.stringData();
    Serial.println("Command from Firebase: " + command);

    if (command == "UNLOCK" && !doorOpen) {
      Firebase.RTDB.setString(&fbdo, "/door_lock/access", "Yes");
      unlockDoor();
    }
  } else {
    Serial.println("Failed to read Firebase: " + fbdo.errorReason());
  }

  delay(1000);
}