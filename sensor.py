"""
=============================================================
  SMART CITY SENSOR — sensor.py
=============================================================
  DS Concepts visible here:
    1. RPC / Message Passing → sends JSON over TCP to broker
    2. Lamport Clocks        → each publish increments local clock
=============================================================
Usage:
    python sensor.py traffic
    python sensor.py pollution
    python sensor.py weather
"""

import socket
import threading
import json
import time
import random
import sys

BROKER_HOST = "127.0.0.1"
BROKER_PORT = 9000


# ─────────────────────────────────────────────
#  CONCEPT 2: LOCAL LAMPORT CLOCK (sender side)
# ─────────────────────────────────────────────
class LamportClock:
    def __init__(self):
        self.time = 0
        self._lock = threading.Lock()

    def tick(self):
        with self._lock:
            self.time += 1
            return self.time

    def update(self, received):
        with self._lock:
            self.time = max(self.time, received) + 1
            return self.time


# ─────────────────────────────────────────────
#  EVENT TEMPLATES PER SENSOR TYPE
# ─────────────────────────────────────────────
EVENTS = {
    "traffic": [
        ("Major accident on Highway 5 — 3 vehicles involved",    "HIGH"),
        ("Heavy congestion detected near City Center junction",   "MEDIUM"),
        ("Signal failure at MG Road & Park Street crossing",      "MEDIUM"),
        ("Vehicle breakdown blocking right lane on Ring Road",    "LOW"),
        ("Rush hour congestion — average speed 12 km/h",         "LOW"),
        ("Wrong-way vehicle detected on Expressway — CRITICAL",  "CRITICAL"),
    ],
    "pollution": [
        ("AQI reached 380 — severe health hazard",               "CRITICAL"),
        ("PM2.5 levels spike to 210 μg/m³ in Zone 4",           "HIGH"),
        ("CO2 concentration above threshold near industrial hub", "HIGH"),
        ("Smog alert issued — visibility below 200m",            "MEDIUM"),
        ("Chemical leak detected near factory district",          "CRITICAL"),
        ("AQI moderate at 85 — safe for outdoor activity",       "LOW"),
    ],
    "weather": [
        ("Flash flood warning: rainfall 120mm in 2 hours",       "CRITICAL"),
        ("Category 2 storm approaching from the coast",          "HIGH"),
        ("Temperature hits 47°C — extreme heat advisory",        "HIGH"),
        ("Wind speed 95 km/h — avoid tall structures",           "MEDIUM"),
        ("Heavy rain expected — possible waterlogging",          "MEDIUM"),
        ("Earthquake tremor 4.2M detected near dam area",        "CRITICAL"),
    ],
}


class SmartCitySensor:
    def __init__(self, sensor_type: str):
        self.sensor_type = sensor_type
        self.clock       = LamportClock()
        self.conn        = None
        self.running     = True

    def connect(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((BROKER_HOST, BROKER_PORT))
        print(f"[SENSOR:{self.sensor_type.upper()}] Connected to broker")

    def publish(self, data: str, severity: str):
        """
        CONCEPT 1: RPC / MESSAGE PASSING
        Build a JSON payload and send over TCP.
        This is a 'remote call' to the broker's PUBLISH handler.

        CONCEPT 2: LAMPORT CLOCK
        Tick clock before every send — ensures causal ordering.
        """
        ts = self.clock.tick()    # <── LAMPORT: increment before send

        event = {
            "type":     "PUBLISH",
            "sensor":   f"{self.sensor_type}-sensor",
            "data":     data,
            "severity": severity,
            "lamport":  ts,        # <── LAMPORT TIMESTAMP attached
        }

        payload = json.dumps(event) + "\n"
        self.conn.sendall(payload.encode())   # <── MESSAGE PASSING over TCP

        print(f"  [LAMPORT:{ts:04d}]  [{severity:8s}]  {data[:60]}")

    def run(self):
        self.connect()
        events = EVENTS.get(self.sensor_type, [])
        print(f"\n{'='*60}")
        print(f"  SENSOR: {self.sensor_type.upper()}  |  Events: {len(events)}")
        print(f"  Lamport clock starts at 0, increments each publish")
        print(f"{'='*60}\n")

        while self.running:
            # Pick a random event from this sensor's pool
            data, severity = random.choice(events)

            # Inject random anomalies to make it interesting
            if random.random() < 0.1:
                severity = "CRITICAL"
                data = "⚠ EMERGENCY: " + data

            self.publish(data, severity)

            # Sensors fire every 3–8 seconds
            delay = random.uniform(3, 8)
            time.sleep(delay)


if __name__ == "__main__":
    sensor_type = sys.argv[1] if len(sys.argv) > 1 else "traffic"
    if sensor_type not in EVENTS:
        print(f"Unknown sensor type. Choose: {list(EVENTS.keys())}")
        sys.exit(1)

    sensor = SmartCitySensor(sensor_type)
    try:
        sensor.run()
    except KeyboardInterrupt:
        print(f"\n[SENSOR:{sensor_type}] Shutting down.")
