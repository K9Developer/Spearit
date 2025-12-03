typedef enum {
    Network_SendPacket = 0,
    Network_ReceivePacket = 1,
    Network_ReceiveConnection = 2,
    Network_CreateConnection = 3,

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

    Event_None = 13
} EventType;