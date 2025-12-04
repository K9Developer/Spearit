cargo build --target-dir=./target --package scout_wrapper --bin scout_wrapper --profile dev && sudo ./target/debug/scout_wrapper
rm -f /dev/shm/scout_shared_memory_loader_write
rm -f /dev/shm/scout_shared_memory_wrapper_write