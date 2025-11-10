#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

char LICENSE[] SEC("license") = "GPL";

// Attach point: tracepoint "syscalls:sys_enter_execve"
SEC("tracepoint/syscalls/sys_enter_execve")
int handle_execve(struct trace_event_raw_sys_enter *ctx)
{
    // Upper 32 bits = PID, lower 32 bits = TID
    __u64 pid_tgid = bpf_get_current_pid_tgid();
    __u32 pid = pid_tgid >> 32;

    bpf_printk("Hello from eBPF, pid=%d\n", pid);
    return 0;
}