#pragma once
#include "constants.h"

typedef __u64 __u128;

typedef struct {
        unsigned long long full_size;
        unsigned long long sample_size;
        unsigned char sample_data[MAX_PAYLOAD_SIZE];
} PayloadBuffer;

typedef struct {
    unsigned long long violated_rule_id;
    unsigned char violation_type;
    unsigned int violation_response;

    unsigned short protocol;
    unsigned long long timestamp_ns;
    unsigned char is_connection_establishing;
    unsigned char direction;

    struct {
        unsigned int pid;
        char name[MAX_PROCESS_NAME_LENGTH];
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

typedef struct {
    unsigned char names[MAX_NETWORK_RECORDS][MAX_NETWORK_RECORD_NAME_LENGTH];  // padded with zeros
    unsigned int counts[MAX_NETWORK_RECORDS];
    unsigned int current_size;
} NetworkContacts;

typedef struct {
    NetworkContacts mac_contacts;
} NetworkInfo;