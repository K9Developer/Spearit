// TODO: build.rs should build from file got from server (eBPF will also use) so no need to update all for each change
#[repr(C)]
#[derive(Clone,Copy)]
pub enum EventType {
    Network_ReceiveConnection = 0,
    Network_SendPacket = 1,
    Network_ReceivePacket = 2,

    Process_Start = 3,
    Process_Exit = 4,
    Process_AccessMemory = 5,

    File_Open = 6,
    File_Modify = 7,
    File_Delete = 8,
    File_Created = 9,

    System_LoginAttempt = 10,

    Agent_Heartbeat = 11,
    Agent_Disconnect = 12,

    None = 13
}