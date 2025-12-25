import threading
from typing import Callable
from models.connection.connection import Connection
import socket
from enum import Enum
from models.connection.fields import Fields
from models.connection.messages.handshake import HandshakeMessage

class SocketServerEvent(Enum):
    CONNECTION_ACCEPTED = 0
    CONNECTION_TERMINATED = 1
    MESSAGE_RECEIVED = 2
    MESSAGE_SENT = 3
    CONNECTION_ESTABLISHED = 4
    CONNECTION_FAILED_TO_ESTABLISH = 5

CALLBACK_TYPE = Callable[[SocketServerEvent, Connection, Fields], None]

class SocketServer:

    clients: list[Connection]
    socket_: socket.socket

    def __init__(self, host: str, port: int) -> None:
        self.clients = []
        print(f"Starting Socket Server on {host}:{port}...")
        self.socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_.bind((host, port))
        self.socket_.listen()
        self.callbacks: dict[SocketServerEvent, list[CALLBACK_TYPE]] = {event: [] for event in SocketServerEvent}

    def __handle_callback(self, event: SocketServerEvent, connection: Connection, fields: Fields) -> None:
        for callback in self.callbacks[event]:
            callback(event, connection, fields)

    # callback will get event, connection, and the fields
    def register_callback(self, event: SocketServerEvent | None, callback: CALLBACK_TYPE) -> None:
        if event is None:
            for ev in SocketServerEvent:
                self.callbacks[ev].append(callback)
        else:
            self.callbacks[event].append(callback)

    def handle_client(self, connection: Connection) -> None:
        def __client_loop():
            try:
                while True:
                    fields = connection.recv_fields()
                    if connection.recv_msg_callback:
                        connection.recv_msg_callback(connection, fields)
            except ConnectionError:
                connection.kill()
                self.__handle_callback(SocketServerEvent.CONNECTION_TERMINATED, connection, Fields([]))
            # except Exception as e:
            #     print(f"Client loop error: {e}")

        threading.Thread(target=__client_loop, daemon=True).start()

    def accept_clients(self) -> None:
        def __accept_loop():
            while True:
                client_socket, addr = self.socket_.accept()
                connection = Connection()
                connection.socket_ = client_socket
                connection.addr = addr
                self.__handle_callback(SocketServerEvent.CONNECTION_ACCEPTED, connection, Fields([]))
                connection.callback_send_message(lambda conn, fields: self.__handle_callback(SocketServerEvent.MESSAGE_SENT, conn, fields))
                connection.callback_recv_message(lambda conn, fields: self.__handle_callback(SocketServerEvent.MESSAGE_RECEIVED, conn, fields))

                success = HandshakeMessage.handle(connection)
                if success:
                    self.clients.append(connection)
                    self.__handle_callback(SocketServerEvent.CONNECTION_ESTABLISHED, connection, Fields([]))
                    self.handle_client(connection)
                else:
                    connection.kill()
                    self.__handle_callback(SocketServerEvent.CONNECTION_FAILED_TO_ESTABLISH, connection, Fields([]))

        threading.Thread(target=__accept_loop, daemon=True).start()
                
        