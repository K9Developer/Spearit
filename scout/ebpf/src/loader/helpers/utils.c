#include <bpf/libbpf.h>
#include "logger.h"
#include <constants.h>
#include <rule.h>
#include "scout.h"

typedef enum {
    RULE_TYPE_PACKET,
    RULE_TYPE_FILE,
    RULE_TYPE_PROCESS,
    RULE_TYPE_NONE
} RuleType;

void pid_to_name(__u32 pid, char *name_buf, size_t buf_size)
{
    if (!name_buf || buf_size == 0) return;

    char proc_path[256] = {0};
    snprintf(proc_path, sizeof(proc_path), "/proc/%u/comm", pid);
    FILE *f = fopen(proc_path, "r");
    if (f) {
        if (fgets(name_buf, buf_size, f) != NULL) {
            size_t len = strlen(name_buf);
            if (len > 0 && name_buf[len - 1] == '\n') {
                name_buf[len - 1] = '\0';
            }
        }
        fclose(f);
    } else {
        snprintf(name_buf, buf_size, "N/A");
    }
}

struct bpf_object * load_object(const char *filename)
{
    struct bpf_object *obj_file = NULL;
    int err;

    obj_file = bpf_object__open_file(filename, NULL);
    if (libbpf_get_error(obj_file)) {
        err = libbpf_get_error(obj_file);
        log_error("Failed to open BPF object: %s", strerror(-err));
        return NULL;
    }

    err = bpf_object__load(obj_file);
    if (err) {
        log_error("Failed to load BPF object: %s", strerror(-err));
        return NULL;
    }

    return obj_file;
}

struct ring_buffer* get_ringbuf_map(struct bpf_object *obj, const char* map_name, ring_buffer_sample_fn callback)
{
    int map_fd = bpf_object__find_map_fd_by_name(obj, map_name);
    if (map_fd < 0) {
        log_error("Failed to find map %s: %s", map_name, strerror(-map_fd));
        return NULL;
    }

    struct ring_buffer *rb = ring_buffer__new(map_fd, callback, NULL, NULL);
    if (libbpf_get_error(rb)) {
        log_error("Failed to create ring buffer for %s: %s", map_name, strerror(-libbpf_get_error(rb)));
        return NULL;
    }

    return rb;
}

int get_array_map_fd(struct bpf_object *obj, const char* map_name)
{
    int map_fd = bpf_object__find_map_fd_by_name(obj, map_name);
    if (map_fd < 0) {
        log_error("Failed to find map %s: %s", map_name, strerror(-map_fd));
        return -1;
    }
    return map_fd;
}

RuleType get_rule_type(CompiledRule* rule)
{
    if (!rule) return RULE_TYPE_NONE;
    if (rule->conditions.length == 0) return RULE_TYPE_NONE;
    if (rule->event_types[0] == Event_None) return RULE_TYPE_NONE;
    if (rule->id == 0) return RULE_TYPE_NONE;

    EventType first_event = rule->event_types[0]; // should match the rest too
    if (first_event >= Network_SendPacket && first_event <= Network_CreateConnection) {
        return RULE_TYPE_PACKET;
    } else if (first_event >= File_Open && first_event <= File_Created) {
        return RULE_TYPE_FILE;
    } else if (first_event >= Process_Start && first_event <= Process_AccessMemory) {
        return RULE_TYPE_PROCESS;
    } else {
        return RULE_TYPE_NONE;
    }
}

void sync_rules(int packet_rules_map_fd)
{

    log_debug("Synchronizing rules...");
    update_rules(); // grab latest rules from wrapper
    CompiledRule* rules = get_rules();
    log_debug("Fetched latest rules from wrapper.");

    for (int ri = 0; ri < MAX_RULES; ri++) {

        // decide the map fd to give the rule to
        RuleType type = get_rule_type(&rules[ri]);

        int map_fd = type == RULE_TYPE_PACKET ? packet_rules_map_fd : -1;
        if (map_fd < 0 && rules[ri].id != 0) {
            log_warn("No valid map found for rule ID %llu at index %d, skipping", rules[ri].id, ri);
            continue;
        }

        if (rules[ri].id == 0) {
            int del_err = bpf_map_delete_elem(map_fd, &ri);
            if (del_err && del_err != -2 && del_err != -9) log_error("Failed to delete rule at index %d from BPF map: %s (%d)", ri, strerror(-del_err), -del_err);
            else if (del_err != -9) log_debug("Deleted rule at index %d from BPF map", ri);
        } else {
            int upd_err = bpf_map_update_elem(map_fd, &ri, &rules[ri], BPF_ANY);
            if (upd_err) log_error("Failed to update rule ID %llu at index %d in BPF map: %s", rules[ri].id, ri, strerror(-upd_err));
            else log_debug("Updated rule ID %llu at index %d in BPF map (%s)", rules[ri].id, ri, type == RULE_TYPE_PACKET ? "Packet" : type == RULE_TYPE_FILE ? "File" : type == RULE_TYPE_PROCESS ? "Process" : "Unknown");
        }
    }

    log_info("Rule synchronization complete.");
    
}