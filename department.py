import socket
import json
import sys


def main():
    # Validate command-line arguments
    if len(sys.argv) != 3:
        print("Usage: python department.py <department_name> <topic>")
        sys.exit(1)

    department_name = sys.argv[1]
    topic = sys.argv[2]

    # Initialize Lamport clock
    lamport_clock = 0

    try:
        # Create persistent TCP socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(("localhost", 9000))

        # Send SUBSCRIBE message immediately
        subscribe_message = {
            "type": "SUBSCRIBE",
            "department": department_name,
            "topic": topic
        }

        client_socket.sendall(
            (json.dumps(subscribe_message) + "\n").encode("utf-8")
        )

        print(f"Registered to topic '{topic}' as '{department_name}'")

        # Buffer for incoming stream data
        buffer = ""

        # Infinite listening loop
        while True:
            data = client_socket.recv(1024)

            # Connection closed
            if not data:
                print("Broker connection closed.")
                break

            buffer += data.decode("utf-8")

            # Process newline-delimited JSON messages
            while "\n" in buffer:
                message, buffer = buffer.split("\n", 1)

                if not message.strip():
                    continue

                try:
                    event = json.loads(message)

                    # Only process EVENT messages
                    if event.get("type") != "EVENT":
                        continue

                    received_lamport = event.get("lamport", 0)

                    # Lamport clock update rule
                    lamport_clock = max(
                        lamport_clock,
                        received_lamport
                    ) + 1

                    # Extract event data
                    topic_name = event.get("topic", "unknown")
                    event_data = event.get("data", "No Data")
                    tx_id = event.get("tx_id")

                    # Critical event handling
                    if tx_id:
                        print(
                            f"[RECEIVED CRITICAL ALERT] "
                            f"Txn ID: {tx_id} | "
                            f"Data: {event_data}"
                        )

                        # Generate ACK
                        ack_message = {
                            "type": "ACK",
                            "department": department_name,
                            "tx_id": tx_id,
                            "lamport": lamport_clock
                        }

                        client_socket.sendall(
                            (json.dumps(ack_message) + "\n").encode("utf-8")
                        )

                        print(
                            f"[SENT ACK] Responding to transaction "
                            f"confirmation {tx_id} "
                            f"at Lamport Time: {lamport_clock}"
                        )

                    else:
                        print(
                            f"[RECEIVED] Topic: {topic_name} | "
                            f"Data: {event_data} | "
                            f"Updated Lamport Clock: {lamport_clock}"
                        )

                except json.JSONDecodeError:
                    print(f"Invalid JSON received: {message}")

    except ConnectionRefusedError:
        print("ERROR: Could not connect to broker on localhost:9000")

    except KeyboardInterrupt:
        print("\nDisconnected from broker.")

    except Exception as e:
        print(f"Unexpected error: {e}")

    finally:
        try:
            client_socket.close()
        except:
            pass


if __name__ == "__main__":
    main()