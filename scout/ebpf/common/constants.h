#pragma once

#define SHARED_MEMORY_PATH_WRITE "scout_shared_memory_1"
#define SHARED_MEMORY_PATH_READ "scout_shared_memory_2"

#define WRAPPER_SHM_KEY 0xDEADBEEFDEADBEEF

// Rules
#define MAX_CONDITION_RAW_VALUE_LENGTH 32
#define MAX_CONDITIONS 7 // per rule
#define MAX_RULES 24
#define MAX_RESPONSES 5

#define VIOLATION_TYPE_PACKET 0
#define VIOLATION_TYPE_CONNECTION 1

// Shared Mem
#define MAX_SHARED_DATA_SIZE 1024
#define SHARED_DATA_LENGTH_SIZE 8
#define REQUEST_ID_SIZE 4

#define MAX_PAYLOAD_SIZE 128

#define DIRECTION_INBOUND 0
#define DIRECTION_OUTBOUND 1
#define CATEGORY_CONNECTION 0
#define CATEGORY_PACKET 1

#ifndef AF_INET
#define AF_INET 2
#endif
#ifndef AF_INET6
#define AF_INET6 10
#endif
#ifndef ETH_ALEN
#define ETH_ALEN	6
#endif
#ifndef ETH_P_ARP
#define ETH_P_ARP    0x0806
#endif
#ifndef ETH_P_IP
#define ETH_P_IP     0x0800
#endif
#ifndef ETH_P_IPV6
#define ETH_P_IPV6   0x86DD
#endif

#define TC_HANDLE 0x1
#define TC_PRIORITY 0xC02F