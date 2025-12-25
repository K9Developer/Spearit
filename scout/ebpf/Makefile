BPF_CLANG = clang
BUILD_DIR = build

SHARED_FLAGS = -Icommon -Icommon/report -Icommon/rule -Icommon/scout
BPF_FLAGS = -O2 -g -target bpf -Iinclude/bpfs $(SHARED_FLAGS)
LOADER_FLAGS = -Iinclude/loader -Iinclude/scout -Iinclude/logger

LOADER_SRCS = $(wildcard src/loader/**/*.c)
SCOUT_SRCS = $(wildcard src/scout/*.c)
EXTRA_SRCS = src/logger/logger.c

all: loader_spearit packet_scout.bpf.o

packet_scout.bpf.o: src/bpfs/network/packet_scout.bpf.c
	$(BPF_CLANG) $(BPF_FLAGS) -c $< -o $(BUILD_DIR)/$@

loader_spearit: $(LOADER_SRCS) $(SCOUT_SRCS) $(EXTRA_SRCS)
	cc -O2 -g src/loader/loader.c $(LOADER_SRCS) $(SCOUT_SRCS) $(EXTRA_SRCS) -o $(BUILD_DIR)/loader_spearit -lbpf -lelf -lz $(SHARED_FLAGS) $(LOADER_FLAGS)
clean:
	rm -f $(BUILD_DIR)/*.o $(BUILD_DIR)/loader_spearit