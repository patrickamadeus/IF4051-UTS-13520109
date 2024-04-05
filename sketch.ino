// NOTE: PLEASE RUN THIS IN ARDUINO IDE AND DOWNLOAD THE SUBSEQUENT LIBRARIES USED!

#include <WiFi.h>
#include <PubSubClient.h>
#include <HTTPClient.h>

const char* ssid = ""; // TODO: Change this to your WiFi SSID
const char* password = ""; // TODO: Change this to your WiFi password
const char* mqtt_server = "broker.emqx.io";
const int mqtt_port = 1883;
const char* mqtt_username = "emqx";
const char* mqtt_password = "public";
const char* topic = "esp32/test13520109";
const int led_pin = 2;
const int button_pin = 0;
const int delay_interval = 5000;
int prev_millis = 0;
const uint16_t keepAliveSec = 300000;

int USER_ID;
const String ENDPOINT = "http://<YOURHOST>:<YOURPORT>"; // TODO: Change this to your server's IP address
int prevButtonState = HIGH;
unsigned long initLoginMillis;
int sec = 15;

bool authenticated = false;
bool publishWelcome = false;

WiFiClient wifiClient;
PubSubClient client(wifiClient);
HTTPClient http;

void setupWifi() {
  // Connect to WiFi network
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("Connected");


  // print the SSID of the network you're attached to:
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  // print your WiFi shield's IP address:
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);
}

void reconnect() {
  if (!client.connected()) {
    client.setServer(mqtt_server, mqtt_port);

    while (!client.connected()) {
      String client_id = "esp32-client-";
      client_id += String(WiFi.macAddress());
      client.connect(client_id.c_str(), mqtt_username, mqtt_password);
    }
    client.subscribe(topic);
  }

  String msg = "Client connection status: " + String(client.connected());
  Serial.println(msg);


}

void setupMQTT() {
    // Set-up broker (Public)
  client.setServer(mqtt_server, mqtt_port);
  while (!client.connected()) {
    String client_id = "esp32-client-";
    client_id += String(WiFi.macAddress());
    Serial.printf("The client %s connects to the public mqtt broker\n", client_id.c_str());
    if (client.connect(client_id.c_str(), mqtt_username, mqtt_password)) {
      Serial.println("Public emqx mqtt broker connected");
    } else {
      Serial.print("failed with state ");
      Serial.print(client.state());
      delay(2000);
    }
  }
  
  // publish and subscribe
  client.publish(topic, "Hi EMQX I'm Digital Payment System ^^ ^^");
  client.publish(topic, "Please enter UserID & PIN with id:pin format! You have 15 seconds to enter the correct combination!");
  client.subscribe(topic);


  client.setKeepAlive(keepAliveSec);

  initLoginMillis = millis();
}

void setup() {
  Serial.begin(115200);
  pinMode(led_pin, OUTPUT);
  pinMode(button_pin, INPUT_PULLUP);

  setupWifi();
  setupMQTT();

  client.setCallback(login_callback);
}

void login_callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message received: [");
  Serial.print(topic);
  Serial.print("] ");

  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();

  String message = String((char*)payload);
  int delimiterIndex = message.indexOf(':');
  
  if (delimiterIndex != -1) {
    String user_id = message.substring(0, delimiterIndex);
    String pin = message.substring(delimiterIndex + 1);

    if (authenticateUser(user_id.toInt(), pin.toInt())) {
      Serial.println("Authentication successful");
      authenticated = true;
      USER_ID = user_id.toInt();
    } else {
      Serial.println("Authentication failed");
    }
  }
}

void led_success(int led_pin, int total_time) {
  digitalWrite(led_pin, HIGH);
  delay(total_time);
  digitalWrite(led_pin, LOW);
}

void led_failed(int led_pin, int total_time, int delay_time) {
  for (int i = 0; i < (int)total_time / (int)delay_time; i++) {
    digitalWrite(led_pin, i % 2 == 0 ? HIGH : LOW);
    delay(delay_time);
  }
  digitalWrite(led_pin, LOW);  // turn the LED off by making the voltage LOW
}

bool authenticateUser(int user_id, int pin) {
  Serial.println("making LOGIN POST request");
  String serverPath = ENDPOINT + "/login?" + "id=" + String(user_id) + "&pin=" + String(pin);

  http.begin(wifiClient, serverPath.c_str());
  http.addHeader("Content-Type", "application/json");

  int httpResponseCode = http.POST(String("{}"));

  http.end();
  return httpResponseCode == 200;
}


int getBalance(int user_id) {
  Serial.println("making GET request");
  String serverPath = ENDPOINT + "/get_balance/" + String(user_id);

  http.begin(wifiClient, serverPath.c_str());

  int httpResponseCode = http.GET();

  Serial.println(httpResponseCode);

  if (httpResponseCode == 200) {
    String payload = http.getString();

    // Find the position of the opening and closing braces to extract the balance value
    int startPos = payload.indexOf(':') + 1;
    int endPos = payload.indexOf('}');
    String balanceString = payload.substring(startPos, endPos);
    int balance = balanceString.toInt();

    http.end();
    return balance;
  } else {
    return -1;
  }
}

int updateBalance(int user_id, int type, int amount){
  Serial.println("making POST request");
  
  String serverPath = ENDPOINT + "/update_balance?" + "user_id=" + String(user_id) + "&type=" + String(type) + "&amount=" + String(amount);

  http.begin(wifiClient, serverPath.c_str());
  http.addHeader("Content-Type", "application/json");

  int httpResponseCode = http.POST(String("{}"));

  http.end();
  return httpResponseCode;
}

void loop() {
  if ((millis() - initLoginMillis <= 15000) && (!authenticated)) {
    client.loop();
    if ((15000.0 - millis() + initLoginMillis) / 1000.0 < sec ){
      String countdownMsg = String(sec) + " seconds left.";
      Serial.println(countdownMsg);
      sec--;
      
      digitalWrite(led_pin, HIGH);
      delay(50);
      digitalWrite(led_pin, LOW);
      delay(50);
      digitalWrite(led_pin, HIGH);
      delay(50);
    }
    digitalWrite(led_pin, LOW);
  } else {
      if (!authenticated) {
        Serial.println(client.publish(topic, "Authentication Timeout. Restarting Auth!"));
        delay(3000);
        exit(0);
      }

      if (!publishWelcome){
        String welcomeMsg = "Authentication Success! Welcome user " + String(USER_ID);
        Serial.println(client.publish(topic, welcomeMsg.c_str()));
        publishWelcome = true;
      }
      
        int currentButtonState = digitalRead(button_pin);

        if (currentButtonState != prevButtonState){
          if ((currentButtonState == LOW)){
            prev_millis = millis();
            prevButtonState = LOW;
            int currentBalance = getBalance(USER_ID);

            if (currentBalance == -1){
              
                String message = "KENDALA PENGAMBILAN INFORMASI SALDO UNTUK USER_ID " + String(USER_ID);

                led_failed(led_pin, 5000, 250);
            } 
            else {
              String message = "WELCOME, SALDO USER_ID " + String(USER_ID) + " ADALAH: " + String(currentBalance);
              Serial.println(client.connected());
              Serial.println(client.publish(topic, message.c_str()));

              Serial.println("Published message: " + message);
              led_success(led_pin, 5000);

              int updateReturnCode = updateBalance(USER_ID, -1, 20000);

              reconnect();

              switch (updateReturnCode) {
                case 200:
                  message = "TRANSAKSI BERHASIL, SISA SALDO Rp." + String(currentBalance - 20000);
                  Serial.println(client.connected());
                  Serial.println(client.publish(topic, message.c_str()));

                  Serial.println("Published message: " + message);

                  led_success(led_pin, 5000);
                  break;
                case 401:
                  message = "SALDO TIDAK MENCUKUPI, SISA SALDO ANDA SEKARANG Rp." + String(currentBalance);
                  client.publish(topic, message.c_str());
                  Serial.println("Published message: " + message);

                  led_failed(led_pin, 5000, 250);
                  break;
                case 402:
                  message = "Invalid Transaction Type.";
                  client.publish(topic, message.c_str());
                  Serial.println("Published message: " + message);

                  led_failed(led_pin, 5000, 250);
                  break;
                case 404:
                  message = "User not Found 404: " + String(USER_ID);
                  client.publish(topic, message.c_str());
                  Serial.println("Published message: " + message);

                  led_failed(led_pin, 5000, 250);
                  break;
                default:
                  message = "KENDALA TRANSAKSI PENARIKAN UNTUK USER_ID " + String(USER_ID);
                  client.publish(topic, message.c_str());
                  Serial.println("Published message: " + message);

                  led_failed(led_pin, 5000, 250);
                  break;
              }
            }
          }
          else{
            // Update Prev Button State
            prevButtonState = HIGH;
          }
        }

  }
}
