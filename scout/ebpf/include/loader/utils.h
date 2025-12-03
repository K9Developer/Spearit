#pragma once
#include <bpf/libbpf.h>

void pid_to_name(__u32 pid, char *name_buf, size_t buf_size);
struct bpf_object * load_object(const char *filename);
struct ring_buffer* get_ringbuf(struct bpf_object *obj, const char* map_name, ring_buffer_sample_fn callback);