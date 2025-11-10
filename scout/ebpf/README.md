
# Installation
1. Update packages `sudo apt update`
2. Install clang and make with `sudo apt install clang make`
3. Install ebpf `sudo apt install libbpf-dev linux-tools-common linux-libc-dev linux-headers-$(uname -r)`
4. Mount debug for log `sudo mount -t debugfs none /sys/kernel/debug || true`

# Run
1. See logs: `sudo cat /sys/kernel/debug/tracing/trace_pipe`
2. Build `make`
3. Run `sudo build/loader`