#include <stdbool.h>
#include <stdlib.h>
#include <pthread.h>
#include <constants.h>
#include <sys/mman.h>
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include "comms.h"
#include <string.h>
#include "logger.h"

int shared_mem_w_fd;
int shared_mem_r_fd;
SharedComms *shared_mem_in;
SharedComms *shared_mem_out;

size_t last_conversation_id = 0; // will start from 1 so this is null
bool initialized = false;

void init() {
    if (initialized) return;
    shared_mem_w_fd = shm_open(SHARED_MEMORY_PATH_WRITE, O_RDWR, 0600);
    shared_mem_r_fd = shm_open(SHARED_MEMORY_PATH_READ, O_RDWR, 0600);
    if (shared_mem_w_fd == -1 || shared_mem_r_fd == -1) {
        log_error("Failed to open shared memory - wrapper never created it");
        exit(1);
    }
    shared_mem_in = (SharedComms*)mmap(NULL, sizeof(SharedComms), PROT_READ | PROT_WRITE, MAP_SHARED, shared_mem_r_fd, 0);
    shared_mem_out = (SharedComms*)mmap(NULL, sizeof(SharedComms), PROT_READ | PROT_WRITE, MAP_SHARED, shared_mem_w_fd, 0);
    if (shared_mem_in == MAP_FAILED || shared_mem_out == MAP_FAILED) {
        log_error("Failed to map shared memory");
        exit(1);
    }

    initialized = true;
}

void destruct_comms() {
    if (!initialized) return;
    munmap(shared_mem_in, sizeof(SharedComms));
    munmap(shared_mem_out, sizeof(SharedComms));
    close(shared_mem_r_fd);
    close(shared_mem_w_fd);
    shm_unlink(SHARED_MEMORY_PATH_READ);
    shm_unlink(SHARED_MEMORY_PATH_WRITE);
    initialized = false;
}

size_t _shm_write(CommID req, void* extra, size_t len) {
    init();
    pthread_mutex_lock(&shared_mem_out->lock);
    unsigned char *buf = shared_mem_out->data;
    shared_mem_out->size = len;
    shared_mem_out->request_id = req;
    if (extra != NULL) memcpy(shared_mem_out->data, extra, len);
    shared_mem_out->current_conversation_id++;
    pthread_mutex_unlock(&shared_mem_out->lock);
    return shared_mem_out->current_conversation_id-1;
}

RawCommsResponse _shm_read() {
    init();
    printf("Lock address: %p\n", (void*)&shared_mem_in->lock);
    pthread_mutex_lock(&shared_mem_in->lock);
    // todo: maybe make it heap and not stack? (the freeing will be on the user tho)
    RawCommsResponse tmp = (RawCommsResponse){ .size = 0 };
    if (last_conversation_id != shared_mem_in->current_conversation_id) {
        tmp.size = shared_mem_in->size;
        tmp.request_id = shared_mem_in->request_id;
        tmp.current_conversation_id = shared_mem_in->current_conversation_id;
        memcpy(tmp.data, shared_mem_in->data, shared_mem_in->size);
        last_conversation_id = shared_mem_in->current_conversation_id;
    }
    pthread_mutex_unlock(&shared_mem_in->lock);
    return tmp;
}


RawCommsResponse shm_request(CommID req, void* extra, size_t len) {
   size_t convo_id = _shm_write(req, extra, len);
   usleep(100000); // 100 ms
   RawCommsResponse res = _shm_read();
   if (res.current_conversation_id == convo_id) {
        return res;
   }
   return (RawCommsResponse){ .size = 0 };
}


void shm_send(CommID req, void* extra, size_t len) {
   _shm_write(req, extra, len);
}

void _wait_for_wrapper(void) {
    init();
    while (shared_mem_in->key != WRAPPER_SHM_KEY) {
        usleep(100000);
    }
    shared_mem_out->key = LOADER_SHM_KEY;
}