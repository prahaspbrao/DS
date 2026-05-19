import socket
import threading
import json
import uuid
import time
import logging

# Configure basic logging for visibility into broker operations
logging.basicConfig(level=logging.INFO, format='%(asctime)s [BROKER] %(message)s')

class SubscriberRegistry:
    """Thread-safe registry mapping topics to active client sockets."""
    def __init__(self):
        self._lock = threading.Lock()
        self._topics = {}  # Format: { "topic_name": set(client_sockets) }

    def subscribe(self, topic, client_socket):
        with self._lock:
            if topic not in self._topics:
                self._topics[topic] = set()
            self._topics[topic].add(client_socket)
            logging.info(f"Client {client_socket.getpeername()} subscribed to '{topic}'")

    def get_subscribers(self, topic):
        with self._lock:
            # Return a list copy to prevent mutation during iteration
            return list(self._topics.get(topic, []))

    def remove_client(self, client_socket):
        with self._lock:
            for topic, subscribers in self._topics.items():
                if client_socket in subscribers:
                    subscribers.remove(client_socket)


class LamportClock:
    """Central logical clock utilizing the Lamport synchronization rule."""
    def __init__(self):
        self._lock = threading.Lock()
        self._time = 0

    def tick(self):
        """Atomic increment."""
        with self._lock:
            self._time += 1
            return self._time

    def update(self, received_time):
        """clock = max(local, received) + 1"""
        with self._lock:
            self._time = max(self._time, received_time) + 1
            return self._time

    def get_time(self):
        with self._lock:
            return self._time


class TransactionCoordinator:
    """Manages 2PC-lite states for HIGH and CRITICAL priority alerts."""
    def __init__(self):
        self._lock = threading.Lock()
        # Format: tx_id -> {"status": str, "expected": int, "acks": set()}
        self._transactions = {}

    def start_transaction(self, expected_acks):
        tx_id = str(uuid.uuid4())
        with self._lock:
            self._transactions[tx_id] = {
                "status": "PENDING",
                "expected": expected_acks,
                "acks": set()
            }
        
        # Spawn an independent background timer for this transaction
        threading.Thread(target=self._timeout_task, args=(tx_id,), daemon=True).start()
        return tx_id

    def _timeout_task(self, tx_id):
        """Sleeps for 5 seconds and forcefully aborts if pending."""
        time.sleep(5.0)
        with self._lock:
            tx = self._transactions.get(tx_id)
            if tx and tx["status"] == "PENDING":
                tx["status"] = "ABORTED"
                logging.warning(f"Transaction {tx_id} ABORTED due to timeout. Missing dependencies.")

    def ack(self, tx_id, client_id):
        with self._lock:
            tx = self._transactions.get(tx_id)
            if not tx or tx["status"] != "PENDING":
                return False
            
            tx["acks"].add(client_id)
            if len(tx["acks"]) >= tx["expected"]:
                tx["status"] = "COMMITTED"
                logging.info(f"Transaction {tx_id} COMMITTED successfully.")
            return True

    def get_status(self, tx_id):
        with self._lock:
            tx = self._transactions.get(tx_id)
            return tx["status"] if tx else "UNKNOWN"


class BrokerServer:
    """Persistent TCP server handling the network boundaries."""
    def __init__(self, host='0.0.0.0', port=9000):
        self.host = host
        self.port = port
        self.registry = SubscriberRegistry()
        self.clock = LamportClock()
        self.coordinator = TransactionCoordinator()
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(100)
        logging.info(f"Broker bound and listening on {self.host}:{self.port}")
        
        try:
            while True:
                conn, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            logging.info("Broker shutting down manually.")
        finally:
            self.server_socket.close()

    def handle_client(self, conn, addr):
        client_id = f"{addr[0]}:{addr[1]}"
        logging.info(f"Client {client_id} established connection.")
        buffer = ""
        
        try:
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                buffer += data.decode('utf-8')
                
                # Extract line-by-line via trailing \n
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if line:
                        self.process_message(line, conn, client_id)
        except Exception as e:
            logging.error(f"Network error with client {client_id}: {e}")
        finally:
            self.registry.remove_client(conn)
            conn.close()
            logging.info(f"Client {client_id} disconnected.")
    def process_message(self, message_str, conn, client_id):
        try:
            msg = json.loads(message_str)
            
            # --- FIX 1: Match the agreed JSON Contract Keys ---
            msg_type = msg.get('type') 
            client_clock = msg.get('lamport', 0) 

            # Synchronize Lamport clock with incoming message
            current_time = self.clock.update(client_clock)

            if msg_type == 'SUBSCRIBE':
                topic = msg.get('topic')
                self.registry.subscribe(topic, conn)
                
                # Acknowledge subscription
                self._send(conn, {
                    "type": "SUBSCRIBED", 
                    "topic": topic, 
                    "lamport": self.clock.tick()
                })

            elif msg_type == 'PUBLISH':
                # Determine topic (if not explicitly in PUBLISH, infer from sensor name)
                sensor_name = msg.get('sensor', 'unknown-sensor')
                topic = msg.get('topic', sensor_name.split('-')[0]) 
                
                # --- FIX 2: Use data and severity ---
                data = msg.get('data', 'No data')
                severity = msg.get('severity', 'LOW')
                
                subscribers = self.registry.get_subscribers(topic)
                
                # --- FIX 3: Broker converts PUBLISH to EVENT ---
                out_msg = {
                    "type": "EVENT",
                    "sensor": sensor_name,
                    "topic": topic,
                    "data": data,
                    "severity": severity,
                    "lamport": self.clock.tick()
                }

                # Trigger 2PC-lite for HIGH and CRITICAL alerts
                if severity in ['HIGH', 'CRITICAL'] and subscribers:
                    tx_id = self.coordinator.start_transaction(len(subscribers))
                    out_msg["tx_id"] = tx_id
                    logging.info(f"[TXN] BEGIN {tx_id} (Severity: {severity}, Awaiting ACKs: {len(subscribers)})")

                # Fanout message to departments
                for sub_conn in subscribers:
                    self._send(sub_conn, out_msg)

            elif msg_type == 'ACK':
                tx_id = msg.get('tx_id')
                if tx_id:
                    logging.info(f"[ACK] Received for {tx_id} from {client_id}")
                    self.coordinator.ack(tx_id, client_id)

            elif msg_type == 'STATUS':
                # Simple response for the dashboard
                self._send(conn, {
                    "type": "STATUS_REPLY", 
                    "lamport": self.clock.get_time()
                })

        except json.JSONDecodeError:
            logging.error(f"Malformed JSON from {client_id}: {message_str}")
        except Exception as e:
            logging.error(f"Processing error from {client_id}: {e}")

    def _send(self, conn, payload):
        try:
            message = json.dumps(payload) + '\n'
            conn.sendall(message.encode('utf-8'))
        except Exception as e:
            logging.error(f"Failed outbound transmission: {e}")

if __name__ == '__main__':
    BrokerServer().start()