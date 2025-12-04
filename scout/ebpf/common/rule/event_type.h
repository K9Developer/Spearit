typedef enum {
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

    Event_None = 14
} EventType;