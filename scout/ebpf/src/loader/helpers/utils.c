#include <bpf/libbpf.h>

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
        fprintf(stderr, "Failed to open BPF object: %s\n", strerror(-err));
        return NULL;
    }

    err = bpf_object__load(obj_file);
    if (err) {
        fprintf(stderr, "Failed to load BPF object: %s\n", strerror(-err));
        return NULL;
    }

    return obj_file;
}

struct ring_buffer* get_ringbuf(struct bpf_object *obj, const char* map_name, ring_buffer_sample_fn callback)
{
    int map_fd = bpf_object__find_map_fd_by_name(obj, map_name);
    if (map_fd < 0) {
        fprintf(stderr, "Failed to find map %s: %s\n", map_name, strerror(-map_fd));
        return NULL;
    }

    struct ring_buffer *rb = ring_buffer__new(map_fd, callback, NULL, NULL);
    if (libbpf_get_error(rb)) {
        fprintf(stderr, "Failed to create ring buffer for %s: %s\n", map_name, strerror(-libbpf_get_error(rb)));
        return NULL;
    }

    return rb;
}