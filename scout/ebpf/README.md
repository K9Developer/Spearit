
# Installation
1. Update packages `sudo apt update`
2. Install clang and make with `sudo apt install clang make`
3. Install ebpf `sudo apt install libbpf-dev linux-tools-generic linux-cloud-tools-generic linux-libc-dev linux-headers-$(uname -r)`
4. Mount debug for log `sudo mount -t debugfs none /sys/kernel/debug || true`
5. Generate the vmlinux.h `bpftool btf dump file /sys/kernel/btf/vmlinux format c > ./common/vmlinux.h` (`sudo find / -type f -name bpftool 2>/dev/null` to find a version that works)

# Run
1. See logs: `sudo cat /sys/kernel/debug/tracing/trace_pipe`
2. Build `make`
3. Run `sudo build/loader`