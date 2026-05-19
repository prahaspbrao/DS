import socket
import json

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('localhost', 9000))
server.listen(5)

print("=== [TEST] Mock Broker Running on Port 9000 ===")
print("Waiting for Prahas's dashboard to query status...\n")

# Mock database state to send back to Prahas
mock_system_state = {
    "type": "STATUS_REPLY",
    "lamport": 42,
    "events": ["[SENSOR] Traffic data published", "[BROKER] Routed to traffic_police"],
    "subscribers": {"traffic": ["traffic_police"], "weather": ["disaster_mgmt"]},
    "transactions": [{"tx_id": "TX-888", "status": "COMMITTED", "participants": ["traffic_police"]}]
}

while True:
    conn, addr = server.accept()
    data = conn.recv(1024).decode('utf-8')
    if "STATUS" in data:
        conn.sendall((json.dumps(mock_system_state) + "\n").encode('utf-8'))
    conn.close()