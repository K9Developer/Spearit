#![allow(non_camel_case_types)]

// TODO: build.rs should build from file got from server (eBPF will also use) so no need to update all for each change
#[repr(C)]
#[derive(Clone, Copy)]
pub(crate) enum EventType {
    Network_SendPacket = 0,
    Network_ReceivePacket = 1,
    Network_ReceiveConnection = 2,
    Network_CreateConnection = 3,

    Process_Start = 4,
    Process_Exit = 5,
    Process_AccessMemory = 6,

    File_Open = 7,
    File_Modify = 8,
    File_Delete = 9,
    File_Created = 10,

    System_LoginAttempt = 11,

    Agent_Heartbeat = 12,
    Agent_Disconnect = 13,

    Event_None = 14,
}

impl EventType {
    pub fn from_string(value: &str) -> EventType {
        match value {
            "network.send_packet" => EventType::Network_SendPacket,
            "network.receive_packet" => EventType::Network_ReceivePacket,
            "network.receive_connection" => EventType::Network_ReceiveConnection,
            "network.create_connection" => EventType::Network_CreateConnection,
            "process.start" => EventType::Process_Start,
            "process.exit" => EventType::Process_Exit,
            "process.access_memory" => EventType::Process_AccessMemory,
            "file.open" => EventType::File_Open,
            "file.modify" => EventType::File_Modify,
            "file.delete" => EventType::File_Delete,
            "file.created" => EventType::File_Created,
            "system.login_attempt" => EventType::System_LoginAttempt,
            "agent.heartbeat" => EventType::Agent_Heartbeat,
            "agent.disconnect" => EventType::Agent_Disconnect,
            _ => EventType::Event_None,
        }
    }
}
