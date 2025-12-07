#pragma once
#include <bpf/libbpf.h>

void log_debug(const char* format, ...);
void log_info(const char* format, ...);
void log_warn(const char* format, ...);
void log_error(const char* format, ...);
void set_debug_enabled(int enabled);
int log_bpf(enum libbpf_print_level level, const char *format, va_list ap);