sudo tc filter del dev enp89s0 egress
sudo tc filter del dev enp89s0 ingress

make clean && make && sudo ./build/loader_spearit