import socket

# create server at port 1000, public

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(("0.0.0.0", 1000))
    s.listen()
    print("Server listening on port 1000...")
    while True:
        conn, addr = s.accept()
        with conn:
            print(f"Connected by {addr}")
            data = conn.recv(1024)
            if not data:
                break
            print(f"Received data: {data.decode()}")
            conn.sendall(b"Hello, client!")