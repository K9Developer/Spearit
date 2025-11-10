#include <stdio.h>
#include <signal.h>
#include <unistd.h>

#include <bpf/libbpf.h>

static volatile sig_atomic_t exiting = 0;

static void handle_sigint(int sig)
{
    exiting = 1;
}

static int libbpf_print_fn(enum libbpf_print_level level,
                           const char *format, va_list args)
{
    // Forward libbpf logs to stderr
    return vfprintf(stderr, format, args);
}

int main(void)
{
    struct bpf_object *obj = NULL;
    struct bpf_program *prog = NULL;
    struct bpf_link *link = NULL;
    int err;

    libbpf_set_strict_mode(LIBBPF_STRICT_ALL);
    libbpf_set_print(libbpf_print_fn);

    // Open ELF object (hello.bpf.o) and parse BPF sections
    obj = bpf_object__open_file("hello.bpf.o", NULL);
    if (libbpf_get_error(obj)) {
        err = -libbpf_get_error(obj);
        fprintf(stderr, "Failed to open BPF object: %d\n", err);
        return 1;
    }

    // Load all programs and maps into kernel (runs verifier)
    err = bpf_object__load(obj);
    if (err) {
        fprintf(stderr, "Failed to load BPF object: %d\n", err);
        return 1;
    }

    // Find our program by its function name in hello.bpf.c
    prog = bpf_object__find_program_by_name(obj, "handle_execve");
    if (!prog) {
        fprintf(stderr, "Failed to find BPF program\n");
        return 1;
    }

    // Attach to the tracepoint "syscalls:sys_enter_execve"
    link = bpf_program__attach_tracepoint(prog, "syscalls", "sys_enter_execve");
    if (libbpf_get_error(link)) {
        err = -libbpf_get_error(link);
        fprintf(stderr, "Failed to attach BPF program: %d\n", err);
        link = NULL;
        return 1;
    }

    signal(SIGINT, handle_sigint);
    printf("Attached. Now run some commands in another shell.\n");
    printf("Press Ctrl-C here to exit.\n");

    while (!exiting) {
        sleep(1);
    }

    bpf_link__destroy(link);
    bpf_object__close(obj);
    return 0;
}