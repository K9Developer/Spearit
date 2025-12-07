// TODO: build.rs should build from file got from server (eBPF will also use) so no need to update all for each change
#[repr(C)]
#[derive(Clone, Copy)]
pub enum ConditionKey {
    Condition_None = 0,

    Packet_Length = 1,
    Packet_SrcIP = 2,
    Packet_DstIP = 3,
    Packet_SrcPort = 4,
    Packet_DstPort = 5,
    Packet_Payload = 6,
    Packet_Protocol = 7,

    Process_PID = 8,
    Process_Name = 9,
    Process_Path = 10,
    Process_Args = 11,

    Memory_ParentPID = 12,
    Memory_AccessType = 13,
    Memory_AccessAddr = 14,

    File_Path = 15,

    User_Name = 16,
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
