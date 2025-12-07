#pragma once

typedef enum {
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
} ConditionKey;