import network
from umqtt.simple import MQTTClient
from machine import Pin
from time import sleep
import dht
import json
import time

# WiFi
WIFI_SSID = "Wokwi-GUEST"
WIFI_PASSWORD = ""

# MQTT
MQTT_BROKER = "broker.emqx.io"
STUDENT_ID = "bm222mr"
SENSOR_TOPIC = f"lnu/iot/{STUDENT_ID}/sensor"
COMMAND_TOPIC = f"lnu/iot/{STUDENT_ID}/command/led"

# Komponenter
led = Pin(27, Pin.OUT)
sensor = dht.DHT22(Pin(33))

# WiFi-anslutning
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASSWORD)
print("Ansluter till WiFi...")
while not wlan.isconnected():
    sleep(0.5)
print("WiFi ansluten! IP:", wlan.ifconfig()[0])

# Kommandon från dashboard
def on_message(topic, msg):
    data = json.loads(msg)
    if data["state"]:
        led.value(1)
    else:
        led.value(0)

# MQTT-anslutning
client = MQTTClient("esp32", MQTT_BROKER)
client.set_callback(on_message)
client.connect()
client.subscribe(COMMAND_TOPIC)
print("Ansluten till MQTT!")

# Huvudloop
while True:
    sensor.measure()
    temp = sensor.temperature()
    payload = json.dumps({
        "value": temp,
        "timestamp": time.time()
    })
    client.publish(SENSOR_TOPIC, payload)
    print(f"Skickade: {payload}")
    client.check_msg()
    sleep(2)