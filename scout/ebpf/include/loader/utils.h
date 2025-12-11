#pragma once
#include <bpf/libbpf.h>

void pid_to_name(__u32 pid, char *name_buf, size_t buf_size);
struct bpf_object * load_object(const char *filename);
struct ring_buffer* get_ringbuf_map(struct bpf_object *obj, const char* map_name, ring_buffer_sample_fn callback);
int get_array_map_fd(struct bpf_object *obj, const char* map_name);
void sync_rules(int packet_rules_map_fd);