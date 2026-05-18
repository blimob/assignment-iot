import { useEffect, useRef, useState } from "react";
import mqtt from "mqtt";
import axios from "axios";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Title,
  Tooltip,
  Legend
);

const STUDENT_ID = "bm222mr";
const SENSOR_TOPIC = `lnu/iot/${STUDENT_ID}/sensor`;
const COMMAND_TOPIC = `lnu/iot/${STUDENT_ID}/command/led`;
const MQTT_BROKER = "wss://broker.emqx.io:8084/mqtt";
const API_URL = "https://fastapi-production-959b.up.railway.app/api/data";

export default function App() {
  const [labels, setLabels] = useState([]);
  const [values, setValues] = useState([]);
  const [ledState, setLedState] = useState(false);
  const [currentTemp, setCurrentTemp] = useState(null);
  const clientRef = useRef(null);

  useEffect(() => {
    axios.get(API_URL).then((res) => {
      const data = res.data;
      setLabels(data.map((d) => new Date(d.timestamp).toLocaleTimeString()));
      setValues(data.map((d) => d.value));
    });

    const client = mqtt.connect(MQTT_BROKER);
    clientRef.current = client;

    client.on("connect", () => {
      client.subscribe(SENSOR_TOPIC);
    });

    client.on("message", (topic, message) => {
      const data = JSON.parse(message.toString());
      const time = new Date().toLocaleTimeString();
      setCurrentTemp(data.value);
      setLabels((prev) => {
        const updated = [...prev, time];
        return updated.length > 60 ? updated.slice(-60) : updated;
      });
      setValues((prev) => {
        const updated = [...prev, data.value];
        return updated.length > 60 ? updated.slice(-60) : updated;
      });
    });

    return () => client.end();
  }, []);

  const toggleLed = (state) => {
    setLedState(state);
    console.log("skickar kommendo:", COMMAND_TOPIC, JSON.stringify({ state }));
    clientRef.current?.publish(COMMAND_TOPIC, JSON.stringify({ state }));
  };

  const chartData = {
    labels,
    datasets: [
      {
        label: "Temperatur (°C)",
        data: values,
        borderColor: "rgb(255, 99, 132)",
        backgroundColor: "rgba(255, 99, 132, 0.2)",
        tension: 0.3,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: { position: "top" },
      title: { display: true, text: "Temperatur över tid" },
    },
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>IoT Dashboard – {STUDENT_ID}</h1>
      <p>
        Aktuell temperatur: <strong>{currentTemp ?? "..."}°C</strong>
      </p>

      <Line data={chartData} options={options} />

      <div style={{ marginTop: "2rem" }}>
        <h2>LED-kontroll</h2>
        <button
          onClick={() => toggleLed(true)}
          style={{
            marginRight: "1rem",
            padding: "0.5rem 1rem",
            background: "green",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
          }}
        >
          Tänd LED
        </button>
        <button
          onClick={() => toggleLed(false)}
          style={{
            padding: "0.5rem 1rem",
            background: "red",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
          }}
        >
          Släck LED
        </button>
        <p>
          LED är: <strong>{ledState ? "PÅ" : "AV"}</strong>
        </p>
      </div>
    </div>
  );
}