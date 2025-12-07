
#define VERBOSE 1
#define OBJECT_NETWORK_SCOUT_PATH "packet_scout.bpf.o"

#define _GNU_SOURCE
#include <signal.h>
#include <bpf/libbpf.h>
#include <ifaddrs.h>
#include <netinet/in.h>
#include "types.h"
#include <net/if.h>
#include <arpa/inet.h>
#include <dirent.h>
#include <stdlib.h>
#include <string.h>
#include <linux/if_ether.h>
#include <errno.h>
#include "tc_loader.h"
#include "utils.h"
#include "../scout/scout.h"
#include "logger.h"

static volatile sig_atomic_t exiting = 0;
static void handle_sigint(int sig) { exiting = 1; }

int handle_packet_violation(void *ctx, void *data, size_t size)
{
    PacketViolationInfo *pi = data;
    PacketViolationInfo local_pi;
    memcpy(&local_pi, pi, sizeof(PacketViolationInfo));

    pid_to_name(local_pi.process.pid, local_pi.process.name, sizeof(local_pi.process.name));
    log_info("Packet Violation: Rule ID: %llu, Type: %u, Protocol: %u, Process: %s (PID: %u)",
             local_pi.violated_rule_id,
             local_pi.violation_type,
             local_pi.protocol,
             local_pi.process.name,
             local_pi.process.pid);
}


struct bpf_object * load_packet_scout() {
    log_debug("Loading packet scout BPF object...");
    struct bpf_object* obj_file = load_object(OBJECT_NETWORK_SCOUT_PATH);
    if (!obj_file) {
        log_error("Failed to load BPF object file: %s", OBJECT_NETWORK_SCOUT_PATH);
        return NULL;
    }
    log_debug("Loaded BPF object file successfully.");
    log_debug("Finding BPF programs in object...");
    struct bpf_program* prog_in = bpf_object__find_program_by_name(obj_file, "tc_ingress_func");
    if (!prog_in) {
        log_error("Failed to find tc_ingress_func BPF program");
        return NULL;
    }
    log_debug("Found tc_ingress_func BPF program.");
    struct bpf_program* prog_eg = bpf_object__find_program_by_name(obj_file, "tc_egress_func");
    if (!prog_eg) {
        log_error("Failed to find tc_egress_func BPF program");
        return NULL;
    }
    log_debug("Found tc_egress_func BPF program.");

    int prog_in_fd = bpf_program__fd(prog_in);
    int prog_eg_fd = bpf_program__fd(prog_eg);

    log_info("Attaching packet scout TC programs to all interfaces...");
    attach_tc_all_interfaces(obj_file, prog_in_fd, prog_eg_fd);
    return obj_file;
}

int main(int argc, char **argv)
{
    set_debug_enabled(VERBOSE);
    log_info("Starting Scout eBPF loader...");

    libbpf_set_strict_mode(LIBBPF_STRICT_ALL);
    libbpf_set_print(log_bpf);

    log_debug("Setting up signal handlers...");
    signal(SIGINT, handle_sigint);
    signal(SIGTERM, handle_sigint);

    log_debug("Loading packet scout BPF...");
    struct bpf_object *packet_obj_file = load_packet_scout();
    if (!packet_obj_file) return 1;

    log_debug("Setting up packet violation ring buffer...");
    struct ring_buffer *packet_rb = get_ringbuf(packet_obj_file, "packet_violations", handle_packet_violation);
    if (!packet_rb) return 1;

    int err;
    log_info("Initialization complete, entering main loop...");
    log_debug("Waiting for wrapper to signal readiness...");
    wait_for_wrapper();
    log_debug("Wrapper signaled readiness, entering main loop.");
    bool found = false;
    while (!found) {
        RawCommsResponse a = _shm_read();
        printf("Received initial message from wrapper, size: %zu\n", a.size);
        // print data as hex
        for (size_t i = 0; i < a.size; i++) {
            printf("%02x ", a.data[i]);
            found = true;
        }
        printf("\n");
    }
    exit(0);
    while (!exiting) {
        ring_buffer__consume(packet_rb);
        if (err = ring_buffer__consume(packet_rb) < 0) fprintf(stderr, "Error polling ring buffer (packet): %d\n", err);
    }

    log_info("Exiting, cleaning up...");
    ring_buffer__free(packet_rb);
    detach_tc_all_interfaces();
    bpf_object__close(packet_obj_file);
    destruct_scout();
    destruct_comms();
    log_debug("Cleanup complete, exiting now.");

    return 0;
}