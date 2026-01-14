import copy
import threading
from typing import Callable
from models.connection.connection import Connection
import socket
from enum import Enum
from models.connection.fields import Fields
from models.connection.messages.handshake import HandshakeMessage
from models.logger import Logger

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
                    if connection.recv_msg_callback: connection.recv_msg_callback(connection, copy.deepcopy(fields))
            except ConnectionError:
                connection.kill()
                self.__handle_callback(SocketServerEvent.CONNECTION_TERMINATED, connection, Fields([]))
                self.clients.remove(connection)
                Logger.debug(f"Connection terminated with {connection.addr[0]}:{connection.addr[1]} ({len(self.clients)} clients)")
            # except Exception as e:
            #     Logger.error(f"SocketServer: Error in client loop: {e}")

        threading.Thread(target=__client_loop, daemon=True).start()

    def __is_device_connected(self, connection: Connection) -> bool:
        conn_ip = connection.addr[0]
        for client in self.clients:
            if client.addr[0] == conn_ip and client != connection:
                return True
        return False

    def accept_clients(self) -> None: # TODO: err handling
        def __accept_loop():
            while True:
                client_socket, addr = self.socket_.accept()
                connection = Connection()
                connection.socket_ = client_socket
                connection.addr = addr

                if self.__is_device_connected(connection):
                    Logger.warn(f"Connection from {addr[0]}:{addr[1]} rejected: device already connected.")
                    connection.kill()
                    self.__handle_callback(SocketServerEvent.CONNECTION_FAILED_TO_ESTABLISH, connection, Fields([]))
                    continue

                self.__handle_callback(SocketServerEvent.CONNECTION_ACCEPTED, connection, Fields([]))
                connection.callback_send_message(lambda conn, fields: self.__handle_callback(SocketServerEvent.MESSAGE_SENT, conn, fields))
                connection.callback_recv_message(lambda conn, fields: self.__handle_callback(SocketServerEvent.MESSAGE_RECEIVED, conn, fields))

                success = HandshakeMessage.handle(connection)
                if success:
                    Logger.info(f"Connection established with {addr[0]}:{addr[1]} ({len(self.clients)+1} clients)")
                    self.clients.append(connection)
                    self.__handle_callback(SocketServerEvent.CONNECTION_ESTABLISHED, connection, Fields([]))
                    self.handle_client(connection)
                else:
                    Logger.warn(f"Connection failed to establish with {addr[0]}:{addr[1]}")
                    connection.kill()
                    self.__handle_callback(SocketServerEvent.CONNECTION_FAILED_TO_ESTABLISH, connection, Fields([]))
                    self.clients.remove(connection)

        threading.Thread(target=__accept_loop, daemon=True).start()
                
        