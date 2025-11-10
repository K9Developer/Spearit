In dynamic/rules.json we'll have something like:
```json
[
  {
    "id": 0,
    "name": "Detect connection on SSH",
    "enabled": true,
    "priority": 1,
    "event_type": "network.receive_connection",
    "conditions": [
      { "key": "connection.port", "op": "==", "value": "22" },
      { "key": "connection.protocol", "op": "==", "value": "tcp" }
    ],
    "responses": ["alert", "airgap"]
  },
  {
    "id": 1,
    "name": "Detect process memory invasion",
    "enabled": true,
    "priority": 1,
    "event_type": "process.access_memory",
    "conditions": [
      { "key": "memory.pid", "op": "!=", "value": "${process.pid}" }
    ],
    "responses": ["alert", "kill"]
  }
]
```
they will be received from the server.

Event list:
```
network:
    receive_connection
    send_packet
    receive_packet
process:
    start
    exit
    access_memory
file:
    open
    modify
    delete
    created
system:
    login_attempt
agent:
    heartbeat
    disconnect    
```

Value list:
```
connection - available under: network
    connection.src_ip
    connection.dst_ip
    connection.src_port
    connection.dst_port
    connection.protocol
packet - available under: network.send_packet, netowork.receive_packet
    packet.len
    packet.src_ip
    packet.dst_ip
    packet.src_port
    packet.dst_port
    packet.payload
process (the process that activated the event) - available under: process, file
    pid
    name
    path
    args
memory (the memory the process tried to access) - available under: process.access_memory
    parent_pid
    access_type
    access_addr
file - available under: file
    path
user - available under: all
    name
```

Action list:
```
air-gap
kill
isolate
alert

later: add run?

```

number for each action should be pretty good.

Scout Wrapper -> SpearHead protocol:
```
[Total Message Length 8 bytes]
[Field 1 Length 4 bytes]
[Field 1]
[Field 2 Length 4 bytes]
[Field 2]
...
```

Handshake (SH - SpearHead, SW - ScoutWrapper):
```
[SH -> SW] IV, PubKey
[SW -> SH] PubKey

session_key = SHA256(shared_secret || "SpearIT-session")

[SH -> SW] encrypted(timestamp)
[SW -> SH] encrypted(timestamp)
```

