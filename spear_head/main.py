from spear_head.constants import SPEAR_HEAD_WRAPPER_PORT
from spear_head.models.connection.server import Server

def main():
    server = Server("0.0.0.0", SPEAR_HEAD_WRAPPER_PORT)
    server.register_callback(None, lambda event, conn, fields: print(f"Event ({event}) on {conn.addr} - total bytes: {len(fields.to_bytes(False))}"))
    server.accept_clients()
    while True:
        pass


if __name__ == "__main__":
    print(f"Spear Head Server is running on port {SPEAR_HEAD_WRAPPER_PORT}...")
    main()