BPF_CLANG = clang
CFLAGS_BPF = -O2 -g -target bpf \
  -I/usr/include \
  -I/usr/include/x86_64-linux-gnu
BUILD_DIR = build

all: loader hello.bpf.o

hello.bpf.o: test/hello.bpf.c
	$(BPF_CLANG) $(CFLAGS_BPF) -c $< -o $(BUILD_DIR)/$@

loader: loader/loader.c
	cc -O2 -g $< -o $(BUILD_DIR)/loader -lbpf -lelf -lz



# all: packet_filter.bpf.o mem_monitor.bpf.o loader

# packet_filter.bpf.o: xdp/packet_filter.bpf.c common/maps.h
# 	$(BPF_CLANG) $(CFLAGS_BPF) -c $< -o $@

# mem_monitor.bpf.o: memmon/mem_monitor.bpf.c common/maps.h
# 	$(BPF_CLANG) $(CFLAGS_BPF) -c $< -o $@

# loader: loader/main.c
# 	cc -O2 -g -o $@ $< -lbpf -lelf -lz

clean:
	rm -f $(BUILD_DIR)/*.o $(BUILD_DIR)/loader