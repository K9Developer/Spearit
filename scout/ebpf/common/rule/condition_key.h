#pragma once

typedef enum {
    Packet_Length = 5,
    Packet_SrcIP = 6,
    Packet_DstIP = 7,
    Packet_SrcPort = 8,
    Packet_DstPort = 9,
    Packet_Payload = 10,
    Packet_Protocol = 11,

    Process_PID = 12,
    Process_Name = 13,
    Process_Path = 14,
    Process_Args = 15,

    Memory_ParentPID = 16,
    Memory_AccessType = 17,
    Memory_AccessAddr = 18,

    File_Path = 19,

    User_Name = 20,

    Condition_None = 21
} ConditionKey;