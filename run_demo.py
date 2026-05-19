import socket
import threading
import json
import time
import random
import logging
from broker import BrokerServer

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def run_broker():
    """Initializes the background broker daemon."""
    server = BrokerServer(host='127.0.0.1', port=9000)
    server.start()

def simulate_department(dept_name, topics, simulate_latency=False):
    """Simulates a subscribing consumer that acknowledges 2PC transactions."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', 9000))
        
        # Subscribe to assigned topics
        for topic in topics:
            sub_req = {"action": "SUBSCRIBE", "topic": topic, "clock": 0}
            s.sendall((json.dumps(sub_req) + '\n').encode('utf-8'))
        
        buffer = ""
        while True:
            data = s.recv(1024)
            if not data:
                break
            buffer += data.decode('utf-8')
            
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                msg = json.loads(line)
                
                # If a transaction ID is provided, simulate processing and ACK
                if msg.get('action') == 'PUBLISH' and 'tx_id' in msg:
                    tx_id = msg['tx_id']
                    logging.info(f"{dept_name} received {msg['priority']} alert: {msg['payload']}")
                    
                    # Randomly simulate heavy delay to trigger the 5-second Coordinator Timeout 
                    if simulate_latency and random.choice([True, False]):
                        logging.warning(f"{dept_name} is experiencing network delay... (6s sleep)")
                        time.sleep(6) 
                    
                    ack_req = {"action": "ACK", "tx_id": tx_id, "clock": msg.get('clock')}
                    s.sendall((json.dumps(ack_req) + '\n').encode('utf-8'))
                    logging.info(f"{dept_name} sent verification ACK for {tx_id}")
                    
    except Exception as e:
        logging.error(f"{dept_name} failed: {e}")

def simulate_sensor(sensor_name, topic, priority, payload, delay):
    """Simulates a publishing producer."""
    time.sleep(delay)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', 9000))
        
        pub_req = {
            "action": "PUBLISH",
            "topic": topic,
            "priority": priority,
            "payload": f"[{sensor_name}] {payload}",
            "clock": 1
        }
        s.sendall((json.dumps(pub_req) + '\n').encode('utf-8'))
        s.close()
    except Exception as e:
        logging.error(f"{sensor_name} failed: {e}")

if __name__ == '__main__':
    print("--- STARTING 2PC MESSAGE BROKER INTEGRATION DEMO ---\n")
    
    # 1. Start Broker
    threading.Thread(target=run_broker, daemon=True).start()
    time.sleep(1.0) # Allow socket to bind
    
    # 2. Start Subscribing Departments (Dependencies)
    # FireDept is reliable. PoliceDept occasionally has 6-second latency to force an ABORT.
    threading.Thread(target=simulate_department, args=("FireDept", ["critical_zone", "public"], False), daemon=True).start()
    threading.Thread(target=simulate_department, args=("PoliceDept", ["critical_zone"], True), daemon=True).start()
    time.sleep(1.0)
    
    # 3. Fire Test Events
    threading.Thread(target=simulate_sensor, args=("TempSensor", "public", "NORMAL", "72F in lobby", 0), daemon=True).start()
    threading.Thread(target=simulate_sensor, args=("SmokeDetector", "critical_zone", "CRITICAL", "Smoke detected in Sector 4!", 2), daemon=True).start()
    threading.Thread(target=simulate_sensor, args=("IntrusionAlarm", "critical_zone", "HIGH", "Unauthorized access at Gate 2.", 10), daemon=True).start()
    
    # 4. Keep main thread alive while background threads interact
    try:
        time.sleep(20)
        print("\n--- DEMO CONCLUDED ---")
    except KeyboardInterrupt:
        pass