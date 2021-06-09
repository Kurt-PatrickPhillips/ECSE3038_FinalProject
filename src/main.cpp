#include <Arduino.h>
#include <SoftwareSerial.h>
#define DEBUG true

SoftwareSerial esp(10, 11); //RX=10, TX=11

String sendData(String command, const int timeout, boolean debug)
{
  String response = "";

  esp.print(command); //send the reader character to the esp8266

  long int time = millis();

  while ((time + timeout) > millis())
  {
    while (esp.available())
    {
      // The esp has data so display its output to the serial window
      char c = esp.read(); // read the next character
      response += c;
    }
  }

  if (debug)
  {
    Serial.print(response);
  }
  return response;
}

void MpuSetup()
{
  Serial.println("Initialize MPU6050");
  while (!mpu.begin(MPU6050_SCALE_2000DPS, MPU6050_RANGE_2G))
  {
    Serial.println("Could not find a valid MPU6050 sensor, check wiring!");
    delay(500);
  }
  mpu.calibrateGyro();

  mpu.setThreshold(3);
}

int readMpu()
{
  Vector rawGyro = mpu.readRawGyro();
  Vector normGyro = mpu.readNormalizeGyro();

  return (int)rawGyro.YAxis;
}

int getTemperature(int testing)
{
  float voltage, temp;

  if (testing == 0)
  {
    // Read temperature from the LM35 sensor
    voltage = analogRead(LM35) * (5.0 / 1023.0);
    temp = 100 * voltage;
  }
  else
  {
    // Generate random test data
    temp = random(30, 41);
  }

  return (int)temp;
}
String generatePostRequest(String route, String portNumber, int cLength, String pstData)
{
  String requestType = "POST /" + route + " HTTP/1.1\r\n";
  String hostInfo = "Host: 192.168.0.4:" + portNumber + "\r\n";
  String contentType = "Content-Type: application/json\r\n";
  String contentLength = "Content-Length: " + String(cLength) + "\r\n\r\n";
  String postData = pstData + "\r\n\r\n";

  return requestType + hostInfo + contentType + contentLength + postData;
}

String generateCIPSend(int requestLength)
{
  String cipSend = "AT+CIPSEND=" + String(requestLength) + "\r\n";

  return cipSend;
}

String generatePost(String patient_id, float pos, int temp)
{
  String post = "{\"patient_id\": \"" + patient_id + "\", \"position\": " + String(pos) + ", \"temperature\": " + String(temp) + "}\r\n\r\n";

  return post;
}

String getMacAddress()
{
  String response = "";
  response = sendData("AT+CIPSTAMAC?\r\n\r\n", 3000, false);
  return response.substring(42, 59);
}

void setup()
{
  Serial.begin(115200);
  esp.begin(115200);
  // esp reset
  sendData("AT+RST\r\n", 10000, DEBUG);
  // change esp to client mode
  sendData("AT+CWMODE=3\r\n", 10000, DEBUG);
  // list Access points
  //sendData("AT+CWLAP\r\n", 10000, DEBUG);
  //join home AP
  sendData("AT+CWJAP=\"CWC-7961954\",\"Zp8jtpkdmdrb\"\r\n", 10000, DEBUG);
  // IP and MAC
  //   sendData("AT+CIFSR\r\n", 10000, DEBUG);
}

String getMacAddress()
{
  String response = "";
  response = sendData("AT+CIPSTAMAC?\r\n\r\n", 3000, false);
  return response.substring(42, 59);
}

/*******   GYRO Setup   *******/
// 1. Initialize:
Serial.println("Initializing MPU6050...");
MpuSetup();
pinMode(LM35, INPUT);

espMacAddress = getMacAddress();
Serial.print("MAC Address: ");
Serial.println(espMacAddress);
void loop()
{
  int temp;
  int pos;

  pos = readMpu();
  temp = getTemperature(0);

  String postData = generatePost(espMacAddress, pos, temp);
  String postRequest = generatePostRequest("api/record", "5000", postData.length(), postData);
  String CIPSend = generateCIPSend(postRequest.length());

  sendData("AT+CIPSTART=\"TCP\",\"192.168.0.4\",5000\r\n", 3000, DEBUG);
  sendData(CIPSend, 1000, DEBUG);
  sendData(postRequest, 5000, DEBUG);
  //if (Serial.available())
  // {
  //   esp.write(Serial.read());
  // }

  // if (esp.available())
  // {
  //  Serial.write(esp.read());
  // }
}