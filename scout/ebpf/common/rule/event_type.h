typedef enum {
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
} EventType;