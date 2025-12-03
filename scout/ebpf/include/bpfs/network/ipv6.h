#pragma once
#include "utils.h"

static int parse_v6_tcp_packet(struct __sk_buff *skb, __u32 offset, PacketViolationInfo *pv_info) {
    struct tcphdr tcp_packet;
    if (bpf_skb_load_bytes(skb, offset, &tcp_packet, sizeof(tcp_packet)) < 0)
        return 0;

    pv_info->ip.src_port = bpf_ntohs(tcp_packet.source);
    pv_info->ip.dst_port = bpf_ntohs(tcp_packet.dest);

    // Check for connection establishing flags (SYN and not ACK or SYN+ACK)
    pv_info->is_connection_establishing = 0;
    if ((tcp_packet.syn) && !(tcp_packet.ack) || (tcp_packet.syn && tcp_packet.ack))
        pv_info->is_connection_establishing = 1;
        
    // get payload
    offset += (tcp_packet.doff * 4);
    extract_payload(skb, offset, &pv_info->payload);

    return 0;
}

static int parse_v6_udp_packet(struct __sk_buff *skb, __u32 offset, PacketViolationInfo *pv_info) {
    struct udphdr udp_packet;
    if (bpf_skb_load_bytes(skb, offset, &udp_packet, sizeof(udp_packet)) < 0)
        return 0;

    pv_info->ip.src_port = bpf_ntohs(udp_packet.source);
    pv_info->ip.dst_port = bpf_ntohs(udp_packet.dest);

    // UDP is connectionless, so no connection establishing flag
    pv_info->is_connection_establishing = 0;

    // get payload
    offset += sizeof(udp_packet);
    extract_payload(skb, offset, &pv_info->payload);

    return 0;
}

static int parse_v6_icmp_packet(struct __sk_buff *skb, __u32 offset, PacketViolationInfo *pv_info) {
    // ICMP does not have ports, so we set them to 0
    pv_info->ip.src_port = 0;
    pv_info->ip.dst_port = 0;

    // ICMP is connectionless, so no connection establishing flag
    pv_info->is_connection_establishing = 0;

    // get payload
    offset += 8; // ICMP header is 8 bytes
    extract_payload(skb, offset, &pv_info->payload);

    return 0;
}

static __always_inline void load_ipv6_address(struct in6_addr *addr, __u64 ip[2]) {
    __u32 a = addr->in6_u.u6_addr32[0];
    __u32 b = addr->in6_u.u6_addr32[1];
    __u32 c = addr->in6_u.u6_addr32[2];
    __u32 d = addr->in6_u.u6_addr32[3];

    __u64 high = (__u64)a << 32 | (__u64)b;
    __u64 low  = (__u64)c << 32 | (__u64)d;
    ip[0] = low;
    ip[1] = high;
}

static __always_inline int parse_ipv6_packet(struct __sk_buff *skb, struct ethhdr *eth_packet, PacketViolationInfo *pv_info, __u8 direction)
{

    struct ipv6hdr ip6;
    __u32 offset = sizeof(struct ethhdr);

    if (bpf_skb_load_bytes(skb, offset, &ip6, sizeof(ip6)) < 0) return 0;

    pv_info->is_ip = 1;
    pv_info->ip.is_ipv4 = 0;

    if (direction == DIRECTION_OUTBOUND) {
        load_ipv6_address(&ip6.saddr, pv_info->ip.ipv6.src_ip);
        load_ipv6_address(&ip6.daddr, pv_info->ip.ipv6.dst_ip);
    } else {
        load_ipv6_address(&ip6.daddr, pv_info->ip.ipv6.src_ip);
        load_ipv6_address(&ip6.saddr, pv_info->ip.ipv6.dst_ip);
    }

    pv_info->protocol = ip6.nexthdr;
    __u32 l4_off = offset + sizeof(struct ipv6hdr);

    if (ip6.nexthdr == IPPROTO_TCP)
        parse_v6_tcp_packet(skb, l4_off, pv_info);
    else if (ip6.nexthdr == IPPROTO_UDP)
        parse_v6_udp_packet(skb, l4_off, pv_info);
    else if (ip6.nexthdr == IPPROTO_ICMP)
        parse_v6_icmp_packet(skb, l4_off, pv_info);

    return 0;
}