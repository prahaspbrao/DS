import socket
import json
import time
import os
import sys

BROKER_HOST = "localhost"
BROKER_PORT = 9000
INTERVAL = 2.0

def clear_screen():
    """Completely clears the terminal console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def fetch_status():
    """Establishes a quick TCP connection to the broker and fetches system state."""
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Set a short timeout so the dashboard doesn't hang indefinitely if the broker is busy
    client.settimeout(1.5) 
    
    try:
        client.connect((BROKER_HOST, BROKER_PORT))
        request = json.dumps({"type": "STATUS"}) + "\n"
        client.sendall(request.encode('utf-8'))
        
        # Read the response until we hit a newline or EOF
        response_bytes = b""
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            response_bytes += chunk
            if b"\n" in chunk:
                break
                
        return json.loads(response_bytes.decode('utf-8'))
    except (socket.error, json.JSONDecodeError, TimeoutError) as e:
        return None
    finally:
        client.close()

def render_dashboard(state):
    """Parses data and outputs four distinct, cleanly designed visual terminal panels."""
    clear_screen()
    
    # Text styling helper
    BOLD = "\033[1m"
    RESET = "\033[0m"
    
    print("=" * 60)
    print(f"{BOLD}              SMART CITY LIVE DS DASHBOARD                  {RESET}")
    print("=" * 60)
    
    if state is None:
        print(f"\n\033[31m[⚠️ ERROR] Unable to connect to broker at {BROKER_HOST}:{BROKER_PORT}{RESET}")
        print("Retrying automatically in 2 seconds...\n")
        print("=" * 60)
        return

    # Extracting fields matching the mock data contract
    events = state.get("events", [])
    lamport_clock = state.get("lamport", 0)
    subscribers = state.get("subscribers", {})
    transactions = state.get("transactions", [])

    # PANEL 1: Message passing history
    print(f"{BOLD}[PANEL 1: RPC MODEL DATA LOGS]{RESET}")
    if events:
        for event in events:
            print(f" - {event}")
    else:
        print(" - No log entries available.")
    print()

    # PANEL 2: Global/Node clock statuses
    print(f"{BOLD}[PANEL 2: LOGICAL SYSTEM CLOCKS]{RESET}")
    print(f" Current Broker Logical Clock Time: {lamport_clock}")
    print()

    # PANEL 3: Mutex operational logs / Active subscriptions
    print(f"{BOLD}[PANEL 3: MUTEX OPERATIONS REGISTRY]{RESET}")
    if subscribers:
        for topic, subs in subscribers.items():
            print(f" Topic '{topic}' -> Active: {subs}")
    else:
        print(" No active topic locking or subscriptions registered.")
    print()

    # PANEL 4: Distributed transactions log
    print(f"{BOLD}[PANEL 4: DISTRIBUTED TRANSACTIONS LOG (2PC-lite)]{RESET}")
    if transactions:
        for tx in transactions:
            tx_id = tx.get("tx_id", "N/A")
            status = tx.get("status", "UNKNOWN")
            # Enhance status string with a nice UI checkmark
            status_str = f"✅ {status}" if status == "COMMITTED" else status
            print(f" Transaction ID: {tx_id} | Status: {status_str}")
    else:
        print(" No active or finalized distributed transactions.")
        
    print("=" * 60)

def main():
    try:
        while True:
            state = fetch_status()
            render_dashboard(state)
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\nDashboard closed gracefully.")
        sys.exit(0)

if __name__ == "__main__":
    main()