from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv
import os
import json
import time

load_dotenv()

# InfluxDB
INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")

influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)
query_api = influx_client.query_api()

# MQTT
MQTT_BROKER = os.getenv("MQTT_BROKER")
STUDENT_ID = os.getenv("STUDENT_ID")
SENSOR_TOPIC = f"lnu/iot/{STUDENT_ID}/sensor"

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload)
        value = float(data["value"])
        point = Point("temperature") \
            .tag("student", STUDENT_ID) \
            .field("value", value) \
            .time(time.time_ns())
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        print(f"Sparat: {value}")
    except Exception as e:
        print(f"Fel: {e}")

def start_mqtt():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_BROKER, 1883)
    client.subscribe(SENSOR_TOPIC)
    client.loop_start()
    return client

@asynccontextmanager
async def lifespan(app: FastAPI):
    mqtt_client = start_mqtt()
    print("MQTT startat!")
    yield
    mqtt_client.loop_stop()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/data")
def get_data(minutes: int = 30):
    try:
        query = f'''
        from(bucket: "{INFLUX_BUCKET}")
        |> range(start: -{minutes}m)
        |> filter(fn: (r) => r._measurement == "temperature")
        |> filter(fn: (r) => r._field == "value")
        '''
        tables = query_api.query(query, org=INFLUX_ORG)
        result = []
        for table in tables:
            for record in table.records:
                result.append({
                    "timestamp": record.get_time().isoformat(),
                    "value": record.get_value()
                })
        return result
    except Exception as e:
        return {"error": str(e)}