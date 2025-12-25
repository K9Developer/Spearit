#include <stdio.h>
#include "logger.h"
#include <stdarg.h>
#include <bpf/libbpf.h>

#define RESET   ""
#define BOLD    ""
#define D_PRE   "[-]"
#define D_MSG   ""
#define I_PRE   "[*]"
#define I_MSG   ""
#define W_PRE   "[!]"
#define W_MSG   ""
#define E_PRE   "[ERROR]"

int debug_enabled = 0;

void set_debug_enabled(int enabled) {
    debug_enabled = enabled;
}

void log_debug(const char* format, ...) {
    if (!debug_enabled) return;
    va_list args; va_start(args, format);
    printf(D_PRE " "); printf(D_MSG); vprintf(format, args); printf(RESET "\n");
    va_end(args);
}

void log_info(const char* format, ...) {
    va_list args; va_start(args, format);
    printf(I_PRE " "); printf(I_MSG); vprintf(format, args); printf(RESET "\n");
    va_end(args);
}

void log_warn(const char* format, ...) {
    va_list args; va_start(args, format);
    printf(W_PRE " "); printf(W_MSG); vprintf(format, args); printf(RESET "\n");
    va_end(args);
}

void log_error(const char* format, ...) {
    va_list args; va_start(args, format);
    printf(E_PRE " "); vprintf(format, args); printf(RESET "\n");
    va_end(args);
}

int log_bpf(enum libbpf_print_level level, const char *format, va_list ap) {
    if (level == LIBBPF_DEBUG) return 0;
    printf(D_PRE ""); printf(D_MSG " [BPF] ");
    vprintf(format, ap);
    printf(RESET);
    return 0;
}