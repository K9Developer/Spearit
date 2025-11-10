// TODO: build.rs should build from file got from server (eBPF will also use) so no need to update all for each change
#[repr(C)]
#[derive(Clone, Copy)]
pub enum DataKey {
    Connection_SrcIP = 0,
    Connection_DstIP = 1,
    Connection_SrcPort = 2,
    Connection_DstPort = 3,
    Connection_Protocol = 4,

    Packet_Length = 5,
    Packet_SrcIP = 6,
    Packet_DstIP = 7,
    Packet_SrcPort = 8,
    Packet_DstPort = 9,
    Packet_Payload = 10,

    Process_PID = 11,
    Process_Name = 12,
    Process_Path = 13,
    Process_Args = 14,

    Memory_ParentPID = 15,
    Memory_AccessType = 16,
    Memory_AccessAddr = 17,

    File_Path = 18,

    User_Name = 19,

    None = 20
}
