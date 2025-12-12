#pragma once

#include <constants.h>
#include "types.h"

typedef enum {
    ReportNone = 0,
    ReportPacket = 1,
    ReportFile = 2
} ReportType;

typedef union {
    PacketViolationInfo packet_report;
} ReportData;

typedef struct {
    ReportType type;
    ReportData data;
} Report;