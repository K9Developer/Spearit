#pragma once

#include <bpf/libbpf.h>
#include <stdbool.h>

int attach_tc_to_interface_direction(int ifindex, int prog_fd, bool is_ingress);
int attach_tc_to_interface(const char *ifname, int prog_in_fd, int prog_eg_fd);
void attach_tc_all_interfaces(struct bpf_object *obj, int prog_in_fd, int prog_eg_fd);

void detach_tc_to_interface_direction(int ifindex, bool is_ingress);
void detach_tc_interface(const char *ifname);
void detach_tc_all_interfaces();