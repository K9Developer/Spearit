import copy
import socket
from typing import Callable
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from constants.constants import AES_BLOCK_SIZE, SOCKET_FULL_LENGTH_SIZE
from models.connection.fields import FieldType, Fields

class Connection:
    """
    Represents a connection with encryption parameters.
    """

    iv: bytes
    session_key: bytes
    in_encryption_mode: bool
    socket_: socket.socket
    addr: tuple[str, int]
    cipher: Cipher[modes.CBC] | None

    send_msg_callback: Callable[['Connection', Fields], None] | None
    recv_msg_callback: Callable[['Connection', Fields], None] | None

    def callback_send_message(self, callback: Callable[['Connection', Fields], None]) -> None:
        self.send_msg_callback = callback

    def callback_recv_message(self, callback: Callable[['Connection', Fields], None]) -> None:
        self.recv_msg_callback = callback

    def __init__(self) -> None:
        self.iv = b''
        self.session_key = b''
        self.in_encryption_mode = False
        self.socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cipher = None
        self.addr = ("", 0)

    def __get_cipher(self) -> Cipher[modes.CBC]:
        if self.cipher is None:
            self.cipher = Cipher(algorithms.AES(self.session_key), modes.CBC(self.iv))
        return self.cipher

    def __encrypt(self, data: bytes) -> bytes:
        if not self.in_encryption_mode:
            raise RuntimeError("Encryption mode is not enabled.")
        
        cipher = self.__get_cipher()
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(AES_BLOCK_SIZE).padder()
        padded_data = padder.update(data) + padder.finalize()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        return encrypted_data

    def __decrypt(self, data: bytes) -> bytes:
        if not self.in_encryption_mode:
            raise RuntimeError("Encryption mode is not enabled.")
        
        cipher = self.__get_cipher()
        decryptor = cipher.decryptor()
        decrypted_padded_data = decryptor.update(data) + decryptor.finalize()
        
        unpadder = padding.PKCS7(AES_BLOCK_SIZE).unpadder()
        decrypted_data = unpadder.update(decrypted_padded_data) + unpadder.finalize()
        return decrypted_data
    
    def set_timeout(self, timeout: float | None) -> None:
        """
        Sets the timeout for the socket operations.

        Args:
            timeout (float | None): The timeout in seconds. None means no timeout.
        """
        self.socket_.settimeout(timeout)

    def kill(self) -> None:
        """
        Terminates the connection.
        """
        self.socket_.shutdown(socket.SHUT_RDWR)
        self.socket_.close()

    def __recv_exact(self, size: int) -> bytes:
        """
        Receives an exact number of bytes from the socket.

        Args:
            size (int): The number of bytes to receive.
        Returns:
            bytes: The received bytes.
        """
        buffer = bytearray()
        while len(buffer) < size:
            chunk = self.socket_.recv(size - len(buffer))
            if not chunk:
                raise ConnectionError("Socket connection broken")
            buffer.extend(chunk)
        
        return bytes(buffer)
    
    def __send_raw(self, data: bytes) -> None:
        """
        Sends raw data over the socket.

        Args:
            data (bytes): The data to send.
        """
        self.socket_.sendall(data)
    
    def send_fields(self, fields: Fields) -> None:
        """
        Sends Fields over the connection, encrypting if in encryption mode.

        Args:
            fields (Fields): The Fields to send.
        """
        if self.send_msg_callback: self.send_msg_callback(self, fields)
        data = fields.to_bytes(not self.in_encryption_mode)
        if self.in_encryption_mode:
            data = self.__encrypt(bytes(data))
            data = len(data).to_bytes(SOCKET_FULL_LENGTH_SIZE, byteorder="big") + data
        self.__send_raw(bytes(data))

    def recv_fields(self) -> Fields:
        """
        Receives Fields from the connection, decrypting if in encryption mode.

        Returns:
            Fields: The received Fields.
        """
        length_data = self.__recv_exact(SOCKET_FULL_LENGTH_SIZE)
        total_length = int.from_bytes(length_data, byteorder="big")
        data = self.__recv_exact(total_length)
        
        fields = Fields.from_bytes(bytearray(length_data + data))
        if self.in_encryption_mode:
            if len(fields.fields) != 1 or fields.fields[0].type_ != FieldType.RAW:
                raise ValueError("Expected a single RAW field for encrypted data.")
            encrypted_data = bytes(fields.fields[0].value)
            decrypted_data = self.__decrypt(encrypted_data)
            fields = Fields.from_bytes(bytearray(len(decrypted_data).to_bytes(SOCKET_FULL_LENGTH_SIZE, byteorder="big") + decrypted_data))
        if self.recv_msg_callback: self.recv_msg_callback(self, copy.deepcopy(fields))
        return fields