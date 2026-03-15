// procmon.bpf.c
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_core_read.h>

struct task_struct;
extern struct task_struct *bpf_task_from_vpid(__s32 vpid) __ksym;
extern void bpf_task_release(struct task_struct *p) __ksym;

#define TASK_COMM_LEN 16
#define PTRACE_PEEKDATA 2
#define PTRACE_PEEKTEXT 1
#define PTRACE_PEEKUSER 3
#define PTRACE_ATTACH 16
#define PTRACE_SEIZE 169

char LICENSE[] SEC("license") = "GPL";

/* -------- Process exec (start) -------- */
SEC("tracepoint/sched/sched_process_exec")
int tp_sched_process_exec(struct trace_event_raw_sched_process_exec *ctx)
{
    u32 pid = (u32)bpf_get_current_pid_tgid();

    char comm[TASK_COMM_LEN];
    bpf_get_current_comm(&comm, sizeof(comm));

    char fname[128] = {};

    /* __data_loc encodes offset (low 16 bits) and length (high 16 bits) */
    u32 loc = BPF_CORE_READ(ctx, __data_loc_filename);
    u32 off = loc & 0xFFFF;

    const char *fn = (const char *)ctx + off;
    bpf_probe_read_str(fname, sizeof(fname), fn);

    bpf_printk("EXEC: pid=%u comm=%s file=%s\n", pid, comm, fname);
    return 0;
}


SEC("tracepoint/sched/sched_process_exit")
int tp_sched_process_exit(struct trace_event_raw_sched_process_template *ctx)
{
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = (u32)pid_tgid;

    char comm[TASK_COMM_LEN];
    bpf_get_current_comm(&comm, sizeof(comm));

    bpf_printk("EXIT: pid=%u comm=%s\n", pid, comm);
    return 0;
}

SEC("tracepoint/syscalls/sys_enter_process_vm_readv")
int tp_sys_enter_process_vm_readv(struct trace_event_raw_sys_enter *ctx)
{
    u32 self_pid = (u32)bpf_get_current_pid_tgid();
    u32 target_pid = (u32)ctx->args[0];

    if (target_pid == 0 || target_pid == self_pid)
        return 0;

    char comm[TASK_COMM_LEN];
    bpf_get_current_comm(&comm, sizeof(comm));

    char target_comm[TASK_COMM_LEN] = "<?>";

    struct task_struct *t = bpf_task_from_vpid((__s32)target_pid);
    if (t) {
        bpf_core_read(target_comm, sizeof(target_comm), &t->comm);
        bpf_task_release(t);
    }

    bpf_printk("VM_READV: pid=%u comm=%s target_pid=%u target_comm=%s\n",
               self_pid, comm, target_pid, target_comm);
    return 0;
}
/* -------- ptrace (peek/attach often used to read memory) --------
 * long ptrace(long request, long pid, unsigned long addr, unsigned long data);
 * args[0]=request, args[1]=pid
 */
static __always_inline int is_ptrace_read_like(long req)
{
    // Common "read" or attach-related requests
    return req == PTRACE_PEEKDATA ||
           req == PTRACE_PEEKTEXT ||
           req == PTRACE_PEEKUSER ||
           req == PTRACE_ATTACH ||
           req == PTRACE_SEIZE;
}

SEC("tracepoint/syscalls/sys_enter_ptrace")
int tp_sys_enter_ptrace(struct trace_event_raw_sys_enter *ctx)
{
    long req = (long)ctx->args[0];
    u32 target_pid = (u32)ctx->args[1];
    u32 self_pid = (u32)bpf_get_current_pid_tgid();

    if (!is_ptrace_read_like(req))
        return 0;
    if (target_pid == 0 || target_pid == self_pid)
        return 0;

    char comm[TASK_COMM_LEN];
    bpf_get_current_comm(&comm, sizeof(comm));

    char target_comm[TASK_COMM_LEN] = "<?>";

    struct task_struct *t = bpf_task_from_vpid((s32)target_pid);
    if (t) {
        /* task_struct::comm is char[TASK_COMM_LEN] */
        bpf_core_read(target_comm, sizeof(target_comm), &t->comm);
        bpf_task_release(t);
    }

    bpf_printk("PTRACE: pid=%u comm=%s req=%ld target_pid=%u target_comm=%s\n",
               self_pid, comm, req, target_pid, target_comm);
    return 0;
}

