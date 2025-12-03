#pragma once

typedef enum {
    AirGap = 0,
    Kill = 1,
    Isolate = 2,
    Alert = 3,
    Run = 4
} ResponseType;

typedef struct {
    ResponseType type;
} Response;

typedef struct {
    Response responses[MAX_RESPONSES];
    unsigned int length;
} ResponseList;