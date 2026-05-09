import socket

def get_port() -> int:
    while True:
        port_input = input("Port to listen on (default 1000): ").strip()
        if port_input == "":
            return 1000
        try:
            port = int(port_input)
            if 1 <= port <= 65535:
                return port
            else:
                print("Please enter a valid port number between 1 and 65535.")
        except ValueError:
            print("Please enter a valid integer for the port number.")

if __name__ == "__main__":
    port = get_port()
    print(f"Listening on port {port}...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", port))
        s.listen()
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    print(f"Received data: {data.decode('utf-8')}")
