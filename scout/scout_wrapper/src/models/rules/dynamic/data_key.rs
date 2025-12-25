#![allow(non_camel_case_types)]
use bytemuck::{Pod, Zeroable};

// TODO: build.rs should build from file got from server (eBPF will also use) so no need to update all for each change
#[repr(u32)]
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum ConditionKey {
    Condition_None = 0,

    Packet_Length = 1,
    Packet_SrcIP = 2,
    Packet_DstIP = 3,
    Packet_SrcPort = 4,
    Packet_DstPort = 5,
    Packet_Payload = 6,
    Packet_Protocol = 7,
    Packet_IsConnectionEstablishing = 8,

    Process_PID = 9,
    Process_Name = 10,
    Process_Path = 11,
    Process_Args = 12,

    Memory_ParentPID = 13,
    Memory_AccessType = 14,
    Memory_AccessAddr = 15,

    File_Path = 16,

    User_Name = 17,
}

impl ConditionKey {
    pub fn from_string(value: &str) -> ConditionKey {
        match value {
            "packet.length" => ConditionKey::Packet_Length,
            "packet.src_ip" => ConditionKey::Packet_SrcIP,
            "packet.dst_ip" => ConditionKey::Packet_DstIP,
            "packet.src_port" => ConditionKey::Packet_SrcPort,
            "packet.dst_port" => ConditionKey::Packet_DstPort,
            "packet.payload" => ConditionKey::Packet_Payload,
            "packet.protocol" => ConditionKey::Packet_Protocol,
            "packet.is_connection_establishing" => ConditionKey::Packet_IsConnectionEstablishing,
            "process.pid" => ConditionKey::Process_PID,
            "process.name" => ConditionKey::Process_Name,
            "process.path" => ConditionKey::Process_Path,
            "process.args" => ConditionKey::Process_Args,
            "memory.parent_pid" => ConditionKey::Memory_ParentPID,
            "memory.access_type" => ConditionKey::Memory_AccessType,
            "memory.access_addr" => ConditionKey::Memory_AccessAddr,
            "file.path" => ConditionKey::File_Path,
            "user.name" => ConditionKey::User_Name,
            _ => ConditionKey::Condition_None,
        }
    }
}
