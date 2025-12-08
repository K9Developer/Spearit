# cargo build --target-dir=./target --package scout_wrapper --bin scout_wrapper --profile dev && clear &&  sudo ./target/debug/scout_wrapper
RUST_BACKTRACE=1 cargo run --package scout_wrapper --bin scout_wrapper --profile dev
rm -f /dev/shm/scout_shared_memory_loader_write
rm -f /dev/shm/scout_shared_memory_wrapper_write