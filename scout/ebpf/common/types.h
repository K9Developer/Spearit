#pragma once
#include "constants.h"

typedef struct {
        unsigned long long full_size;
        unsigned long long sample_size;
        unsigned char sample_data[MAX_PAYLOAD_SIZE];
} PayloadBuffer;

typedef struct {
    unsigned long long violated_rule_id;
    unsigned char violation_type;

    unsigned short protocol;
    unsigned long long timestamp_ns;
    unsigned char is_connection_establishing;
    unsigned char direction;

    struct {
        unsigned int pid;
        char name[16];
    } process;

    unsigned char src_mac[6];
    unsigned char dst_mac[6];

    unsigned char is_ip;
    struct {
        unsigned short src_port;
        unsigned short dst_port;
        unsigned char is_ipv4;
        union {
            struct { unsigned int src_ip; unsigned int dst_ip; } ipv4;
            struct { unsigned long long src_ip[2]; unsigned long long dst_ip[2]; } ipv6;
        };
    } ip;

    PayloadBuffer payload;
} PacketViolationInfo;