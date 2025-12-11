#![allow(non_camel_case_types)]
use bytemuck::{Pod, Zeroable};

use crate::log_error;

// TODO: build.rs should build from file got from server (eBPF will also use) so no need to update all for each change
#[repr(u32)]
#[derive(Clone, Copy, PartialEq, Eq)]
pub(crate) enum EventType {
    Event_None = 0,

    Network_SendPacket = 1,
    Network_ReceivePacket = 2,
    Network_ReceiveConnection = 3,
    Network_CreateConnection = 4,

    Process_Start = 5,
    Process_Exit = 6,
    Process_AccessMemory = 7,

    File_Open = 8,
    File_Modify = 9,
    File_Delete = 10,
    File_Created = 11,

    System_LoginAttempt = 12,
    Agent_Heartbeat = 13,
    Agent_Disconnect = 14,
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
