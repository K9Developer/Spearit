#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>
#include <bpf/bpf_tracing.h>
#include "types.h"
#include "rule.h"
#include "network/ipv4.h"
#include "network/ipv6.h"
#include "rules.h"
#include "utils.h"

// TODO: ring buf submit - see packets in loader
// TODO: check whats-up with PID

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(key_size, sizeof(__u32)); // order
    __uint(value_size, sizeof(CompiledRule));
    __uint(max_entries, MAX_RULES);
} rules SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, sizeof(PacketViolationInfo) * 1024);
} packet_violations SEC(".maps");

static __always_inline const char* prot_name(__u16 proto)
{
    switch (proto) {
        case IPPROTO_TCP: return "TCP";
        case IPPROTO_UDP: return "UDP";
        case IPPROTO_ICMP: return "ICMP";
        case ETH_P_ARP: return "ARP";
        case ETH_P_IP: return "IP";
        case ETH_P_IPV6: return "IPv6";
        default: return "OTHER";
    }
}

__noinline int print_packet(PacketViolationInfo *pi)
{
    if (!pi) return 0;
    bpf_printk("========================================");
    bpf_printk("VIOLATION: rule_id=%llu type=%u proto=%u (%s)",
               pi->violated_rule_id, pi->violation_type, pi->protocol, prot_name(pi->protocol));
    bpf_printk("timestamp=%llu ns  conn_establishing=%u", pi->timestamp_ns, pi->is_connection_establishing);
    bpf_printk("process: pid=%u", pi->process.pid);
    bpf_printk("MAC %02x:%02x:%02x:%02x:%02x:%02x -> %02x:%02x:%02x:%02x:%02x:%02x", pi->src_mac[0], pi->src_mac[1], pi->src_mac[2], pi->src_mac[3], pi->src_mac[4], pi->src_mac[5], pi->dst_mac[0], pi->dst_mac[1], pi->dst_mac[2], pi->dst_mac[3], pi->dst_mac[4], pi->dst_mac[5]);
    if (!pi->is_ip) {
        bpf_printk("Not an IP packet");
        bpf_printk("----------------------------------------");
        return 0;
    }

    if (pi->ip.is_ipv4) {
        __u32 s = bpf_ntohl(pi->ip.ipv4.src_ip);
        __u32 d = bpf_ntohl(pi->ip.ipv4.dst_ip);
        bpf_printk("IPv4 %u.%u.%u.%u:%u -> %u.%u.%u.%u:%u", (s >> 24) & 0xff, (s >> 16) & 0xff, (s >> 8) & 0xff, s & 0xff, pi->ip.src_port, (d >> 24) & 0xff, (d >> 16) & 0xff, (d >> 8) & 0xff, d & 0xff, pi->ip.dst_port);
    } else {
        __u64 s[2];
        __u64 d[2];

        s[0] = pi->ip.ipv6.src_ip[0];
        s[1] = pi->ip.ipv6.src_ip[1];
        d[0] = pi->ip.ipv6.dst_ip[0];
        d[1] = pi->ip.ipv6.dst_ip[1];

        bpf_printk("IPv6 src = %08x:%08x:%08x:%08x:%08x:%08x:%08x:%08x:%u",
            (unsigned int)(s[1] >> 32), (unsigned int)(s[1] & 0xFFFFFFFF),
            (unsigned int)(s[0] >> 32), (unsigned int)(s[0] & 0xFFFFFFFF),
            (unsigned int)(d[1] >> 32), (unsigned int)(d[1] & 0xFFFFFFFF),
            (unsigned int)(d[0] >> 32), (unsigned int)(d[0] & 0xFFFFFFFF),
            pi->ip.dst_port);

        bpf_printk("IPv6 dst = %08x:%08x:%08x:%08x:%08x:%08x:%08x:%08x:%u",
            (unsigned int)(d[1] >> 32), (unsigned int)(d[1] & 0xFFFFFFFF),
            (unsigned int)(d[0] >> 32), (unsigned int)(d[0] & 0xFFFFFFFF),
            (unsigned int)(s[1] >> 32), (unsigned int)(s[1] & 0xFFFFFFFF),
            (unsigned int)(s[0] >> 32), (unsigned int)(s[0] & 0xFFFFFFFF),
            pi->ip.src_port);
    }

    bpf_printk("Payload preview (8 bytes) (sample:%u, full:%u):", pi->payload.sample_size, pi->payload.full_size);

    __u8 byte = 0;
    int i;
    char a0 = '.', a1 = '.', a2 = '.', a3 = '.';

    for (i = 0; i < 8; i++) {
        byte = 0;

        if (i < pi->payload.sample_size) {
            if (bpf_probe_read_kernel(&byte, sizeof(byte),
                                      &pi->payload.sample_data[i]) != 0) {
                byte = 0;
            }
        }

        char ch = (byte >= 32 && byte <= 126) ? (char)byte : '.';

        switch (i & 3) {
        case 0: a0 = ch; break;
        case 1: a1 = ch; break;
        case 2: a2 = ch; break;
        case 3: a3 = ch; break;
        }

        if ((i & 3) == 3) {
            char ascii_line[5] = { a0, a1, a2, a3, 0 };

            __u8 b0 = 0, b1 = 0, b2 = 0, b3 = 0;
            int base = i - 3;

            if (base + 0 < pi->payload.sample_size)
                bpf_probe_read_kernel(&b0, sizeof(b0),
                                      &pi->payload.sample_data[base + 0]);
            if (base + 1 < pi->payload.sample_size)
                bpf_probe_read_kernel(&b1, sizeof(b1),
                                      &pi->payload.sample_data[base + 1]);
            if (base + 2 < pi->payload.sample_size)
                bpf_probe_read_kernel(&b2, sizeof(b2),
                                      &pi->payload.sample_data[base + 2]);
            if (base + 3 < pi->payload.sample_size)
                bpf_probe_read_kernel(&b3, sizeof(b3),
                                      &pi->payload.sample_data[base + 3]);

            bpf_printk(" %02x %02x %02x %02x  %s",
                       b0, b1, b2, b3, ascii_line);
        }
    }

    bpf_printk("----------------------------------------");
    return 0;
}

int handle_packet(struct __sk_buff *skb, __u8 direction) {
    void *data = (void *)(long)skb->data;
    void *data_end = (void *)(long)skb->data_end;
    struct ethhdr *eth_packet = data;

    // is valid ethernet header
    if ((void *)(eth_packet + 1) > data_end) return 0;
    __u16 proto = eth_packet->h_proto;

    PacketViolationInfo pv_info = {0};

    pv_info.timestamp_ns = bpf_ktime_get_tai_ns();
    pv_info.direction = direction;
    pv_info.process.pid = bpf_get_current_pid_tgid() >> 32;
    pv_info.protocol = bpf_ntohs(proto);
    pv_info.process.name[0] = 'N';
    pv_info.process.name[1] = '/';
    pv_info.process.name[2] = 'A';
    pv_info.process.name[3] = 0;
    __builtin_memcpy(pv_info.src_mac, eth_packet->h_source, 6);
    __builtin_memcpy(pv_info.dst_mac, eth_packet->h_dest, 6);

    if (proto == bpf_htons(ETH_P_IP)) {
        parse_ipv4_packet(skb, eth_packet, &pv_info);
    } else if (proto == bpf_htons(ETH_P_IPV6)) {
        parse_ipv6_packet(skb, eth_packet, &pv_info, direction);
    } else {
        extract_payload(skb, sizeof(struct ethhdr), &pv_info.payload);
    }


    bool has_violation = false;
    __u128 violated_rule_info = evaluate_packet_rules(&rules, &pv_info, &has_violation);
    if (has_violation) {
        pv_info.violated_rule_id = (__u64)(violated_rule_info >> 64);
        __u64 violated_rule_order = (__u64)(violated_rule_info & 0xFFFFFFFFFFFFFFFF);
        pv_info.violation_type = pv_info.is_connection_establishing ? VIOLATION_TYPE_CONNECTION : VIOLATION_TYPE_PACKET;
        print_packet(&pv_info);

        PacketViolationInfo *ev = bpf_ringbuf_reserve(&packet_violations, sizeof(*ev), 0);
        if (!ev) {
            bpf_printk("Failed to reserve ringbuf space for packet violation event\n");
            return 0;
        }
        *ev = pv_info;
        bpf_ringbuf_submit(ev, BPF_RB_FORCE_WAKEUP);

        int res = packet_response(violated_rule_order, &rules);
        bpf_printk("Packet response action: %d", res);
        return res;
    }

    return 0;
}

SEC("tc/ingress")
int tc_ingress_func(struct __sk_buff *skb)
{
    return handle_packet(skb, DIRECTION_INBOUND);
}

SEC("tc/egress")
int tc_egress_func(struct __sk_buff *skb) {
    return handle_packet(skb, DIRECTION_OUTBOUND);
}

char LICENSE[] SEC("license") = "GPL";