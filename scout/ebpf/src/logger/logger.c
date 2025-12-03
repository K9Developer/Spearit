#include <stdio.h>
#include "logger.h"
#include <stdarg.h>

#define RESET   "\x1b[0m"
#define BOLD    "\x1b[1m"
#define D_PRE   "\x1b[1;90m[-]\x1b[0m"
#define D_MSG   "\x1b[90m"
#define I_PRE   "\x1b[1;36m[*]\x1b[0m"
#define I_MSG   "\x1b[37m"
#define W_PRE   "\x1b[1;33m[!]\x1b[0m"
#define W_MSG   "\x1b[93m"
#define E_PRE   "\x1b[1;97;41m[ERROR]"

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