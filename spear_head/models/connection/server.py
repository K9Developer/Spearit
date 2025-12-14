import threading
from typing import Callable
from spear_head.models.connection.connection import Connection
import socket
from enum import Enum
from spear_head.models.connection.fields import Fields
from spear_head.models.connection.messages.handshake import HandshakeMessage

class ServerEvent(Enum):
    CONNECTION_ACCEPTED = 0
    CONNECTION_TERMINATED = 1
    MESSAGE_RECEIVED = 2
    MESSAGE_SENT = 3
    CONNECTION_ESTABLISHED = 4
    CONNECTION_FAILED_TO_ESTABLISH = 5

class Server:

    clients: list[Connection]
    socket_: socket.socket

    def __init__(self, host: str, port: int) -> None:
        self.clients = []
        self.socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_.bind((host, port))
        self.socket_.listen()
        self.callbacks = {event: [] for event in ServerEvent}

    def __handle_callback(self, event: ServerEvent, connection: Connection, fields: Fields) -> None:
        for callback in self.callbacks[event]:
            callback(event, connection, fields)

    # callback will get event, connection, and the fields
    def register_callback(self, event: ServerEvent | None, callback: Callable[[ServerEvent, Connection, Fields], None]) -> None:
        if event is None:
            for ev in ServerEvent:
                self.callbacks[ev].append(callback)
        else:
            self.callbacks[event].append(callback)

    def accept_clients(self) -> None:
        def __accept_loop():
            while True:
                client_socket, addr = self.socket_.accept()
                connection = Connection()
                connection.socket_ = client_socket
                connection.addr = addr
                self.__handle_callback(ServerEvent.CONNECTION_ACCEPTED, connection, Fields([]))
                connection.callback_send_message(lambda conn, fields: self.__handle_callback(ServerEvent.MESSAGE_SENT, conn, fields))
                connection.callback_recv_message(lambda conn, fields: self.__handle_callback(ServerEvent.MESSAGE_RECEIVED, conn, fields))

                success = HandshakeMessage.handle(connection)
                if success:
                    self.clients.append(connection)
                    self.__handle_callback(ServerEvent.CONNECTION_ESTABLISHED, connection, Fields([]))
                else:
                    connection.kill()
                    self.__handle_callback(ServerEvent.CONNECTION_FAILED_TO_ESTABLISH, connection, Fields([]))

        threading.Thread(target=__accept_loop, daemon=True).start()
                
        