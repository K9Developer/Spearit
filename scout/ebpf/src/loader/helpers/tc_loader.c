#include "tc_loader.h"
#include <dirent.h>
#include <stdlib.h>
#include <errno.h>
#include "constants.h"
#include <net/if.h>
#include "logger.h"

int attach_tc_to_interface_direction(int ifindex, int prog_fd, bool is_ingress)
{
    
    int err;
    DECLARE_LIBBPF_OPTS(bpf_tc_hook, hook, .attach_point = is_ingress ? BPF_TC_INGRESS : BPF_TC_EGRESS);
    DECLARE_LIBBPF_OPTS(bpf_tc_opts, attach_dir);
    hook.ifindex = ifindex;
    attach_dir.prog_fd = prog_fd;
   
    err = bpf_tc_hook_create(&hook);
    if (err && err != -EEXIST) {
        log_error("Failed to create TC hook for ifindex %d: %d", ifindex, err);
        return err;
    } else if (err == -EEXIST) {
        log_debug("TC hook already exists for ifindex %d, continuing...", ifindex);
    }

    hook.attach_point = is_ingress ? BPF_TC_INGRESS : BPF_TC_EGRESS;
	attach_dir.flags = BPF_TC_F_REPLACE;
	attach_dir.handle = TC_HANDLE;
	attach_dir.priority = TC_PRIORITY;

    err = bpf_tc_attach(&hook, &attach_dir);
	if (err) {
        log_error("Failed to attach TC program to ifindex %d: %d", ifindex, err);
		return err;
	}

    return  0;
}

int attach_tc_to_interface(const char *ifname, int prog_in_fd, int prog_eg_fd)
{
    int ifindex = if_nametoindex(ifname);
    if (ifindex == 0) {
        log_warn("Invalid interface: %s", ifname);
        return -1;
    }

    int err;
    log_debug("Attaching TC ingress to interface: %s", ifname);
    err = attach_tc_to_interface_direction(ifindex, prog_in_fd, true);
    if (err) return err;
    log_debug("Attaching TC egress to interface: %s", ifname);
    err = attach_tc_to_interface_direction(ifindex, prog_eg_fd, false);
    if (err) return err;

    log_debug("Successfully attached TC programs to interface: %s", ifname);
    return 0;
}

void attach_tc_all_interfaces(struct bpf_object *obj, int prog_in_fd, int prog_eg_fd)
{
    DIR *d = opendir("/sys/class/net");
    if (!d) return;

    struct dirent *de;
    while ((de = readdir(d)) != NULL) {
        if (de->d_name[0] == '.') continue;
        if (!strcmp(de->d_name, "lo")) continue;
        log_debug("Attaching TC programs to interface: %s", de->d_name);
        attach_tc_to_interface(de->d_name, prog_in_fd, prog_eg_fd);
    }

    closedir(d);
}

void detach_tc_to_interface_direction(int ifindex, bool is_ingress) {
    int err;
    DECLARE_LIBBPF_OPTS(bpf_tc_hook, hook, .ifindex = ifindex, .attach_point = is_ingress ? BPF_TC_INGRESS : BPF_TC_EGRESS);
	DECLARE_LIBBPF_OPTS(bpf_tc_opts, opts_info);
    opts_info.handle = TC_HANDLE;
	opts_info.priority = TC_PRIORITY;
    err = bpf_tc_query(&hook, &opts_info);
	if (err) log_debug("No program to detach for ifindex %d (err:%d)", ifindex, err);
    opts_info.prog_fd = 0;
	opts_info.prog_id = 0;
	opts_info.flags = 0;
	err = bpf_tc_detach(&hook, &opts_info);
	if (err) log_error("Cannot detach TC-BPF program id:%d for ifindex %d (err:%d)", opts_info.prog_id, ifindex, err);
}

void detach_tc_interface(const char *ifname)
{
    int err;
    int ifindex = if_nametoindex(ifname);
    if (ifindex == 0) {
        log_warn("Invalid interface: %s", ifname);
        return;
    }

    detach_tc_to_interface_direction(ifindex, true);
    detach_tc_to_interface_direction(ifindex, false);
}

void detach_tc_all_interfaces()
{
    DIR *d = opendir("/sys/class/net");
    if (!d) return;

    struct dirent *de;
    while ((de = readdir(d)) != NULL) {
        if (de->d_name[0] == '.') continue;
        if (!strcmp(de->d_name, "lo")) continue;

        int ifindex = if_nametoindex(de->d_name);
        if (ifindex == 0) continue;
        log_debug("Detaching TC programs from interface: %s", de->d_name);

        detach_tc_interface(de->d_name);
    }

    closedir(d);
}