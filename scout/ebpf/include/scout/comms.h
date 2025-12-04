#pragma once

#include <stdbool.h>
#include <stdlib.h>
#include <pthread.h>
#include <constants.h>
#include <sys/mman.h>
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>

typedef enum {
    REQ_ACTIVE_RULE_IDS, // Request list of active rule IDs
    REQ_RULE_DATA, // Request data for a specific rule
    RES_RULE_VIOLATION, // Response indicating a rule violation
    RES_ACTIVE_RULE_IDS // Response with active rule IDs
} CommID;

typedef struct {
    unsigned char data[MAX_SHARED_DATA_SIZE];
    size_t size;
    size_t current_conversation_id;
    CommID request_id;
} RawCommsResponse;

typedef struct {
    size_t key;
    pthread_mutex_t lock;
    size_t current_conversation_id;
    CommID request_id;
    size_t size;
    unsigned char data[MAX_SHARED_DATA_SIZE];
} SharedComms;

size_t _shm_write(CommID req, void* extra, size_t len);

RawCommsResponse _shm_read();


/**
 * Return of RawCommsResponse.size == 0 is failed / no change
 */
RawCommsResponse shm_request(CommID req, void* extra, size_t len);

void shm_send(CommID req, void* extra, size_t len);

void _wait_for_wrapper(void);
void destruct_comms(void);