#pragma once

#include <constants.h>
#include "types.h"

typedef enum {
    ReportPacket = 0,
    ReportFile = 1
} ReportType;

typedef union {
    PacketViolationInfo packet_report;
} ReportData;

typedef struct {
    ReportType type;
    ReportData data;
} Report;