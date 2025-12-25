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
} ConditionKey;