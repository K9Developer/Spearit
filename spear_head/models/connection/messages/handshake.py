import hashlib
import os
import struct
import time
from models.connection.base_message import BaseMessage
from models.connection.connection import Connection
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from models.connection.fields import FieldType, FieldsBuilder

class HandshakeMessage(BaseMessage):
    
    @staticmethod
    def __handle(conn: Connection) -> bool:
        conn.set_timeout(20)

        # [Server --> Client] IV, PUB
        iv = os.urandom(16)
        conn.iv = iv
        server_priv = x25519.X25519PrivateKey.generate()
        server_pub = server_priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        fields = FieldsBuilder().add_raw_field(iv).add_raw_field(server_pub).build()
        conn.send_fields(fields)

        # [Client --> Server] PUB
        client_pub_raw = conn.recv_fields().consume_field()
        if client_pub_raw is None or client_pub_raw.type_ !=  FieldType.RAW:
            print("Invalid client public key field")
            return False
        client_pub = x25519.X25519PublicKey.from_public_bytes(bytes(client_pub_raw.value))

        # calc sess key
        shared = server_priv.exchange(client_pub)
        h = hashlib.sha256()
        h.update(shared)
        h.update(b"SpearIT-K9Dev")
        session_key = h.digest()  # 32 bytes
        conn.session_key = session_key[:16]  # AES-128
        conn.in_encryption_mode = True

        # [Server --> Client] timestamp encrypted
        now_raw = struct.pack(">Q", int(time.time()))
        fields = FieldsBuilder().add_raw_field(now_raw).build()
        conn.send_fields(fields)

        # [Client --> Server] timestamp encrypted
        client_time_raw = conn.recv_fields().consume_field()
        if client_time_raw is None or client_time_raw.type_ != FieldType.RAW:
            print("Invalid client time field")
            return False
        client_time = struct.unpack(">Q", bytes(client_time_raw.value))[0]
        if abs(client_time - int(time.time())) > 5:
            print(f"Client time difference too large ({abs(client_time - int(time.time()))}s)")
            return False
        
        conn.set_timeout(None)
        return True


    @staticmethod
    def handle(conn: Connection) -> bool:
        try:
            return HandshakeMessage.__handle(conn)
        except Exception as e:
            print(f"Handshake failed: {e}")
            conn.iv = b''
            conn.session_key = b''
            conn.in_encryption_mode = False
            return False