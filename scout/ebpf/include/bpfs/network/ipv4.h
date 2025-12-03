#pragma once
#include "utils.h"
#include <bpf/bpf_endian.h>

static int parse_v4_tcp_packet(struct __sk_buff *skb, __u32 offset, PacketViolationInfo *pv_info) {
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

static int parse_v4_udp_packet(struct __sk_buff *skb, __u32 offset, PacketViolationInfo *pv_info) {
    struct udphdr udp_packet;
    if (bpf_skb_load_bytes(skb, offset, &udp_packet, sizeof(udp_packet)) < 0)
        return 0;

    pv_info->ip.src_port = bpf_ntohs(udp_packet.dest);
    pv_info->ip.dst_port = bpf_ntohs(udp_packet.source);

    // UDP is connectionless, so no connection establishing flag
    pv_info->is_connection_establishing = 0;

    // get payload
    offset += sizeof(udp_packet);
    extract_payload(skb, offset, &pv_info->payload);

    return 0;
}

static int parse_v4_icmp_packet(struct __sk_buff *skb, __u32 offset, PacketViolationInfo *pv_info) {
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

static int parse_ipv4_packet(struct __sk_buff *skb, struct ethhdr *eth_packet, PacketViolationInfo *pv_info) {
    struct iphdr ip_packet;
    __u32 offset = sizeof(struct ethhdr);
    if (bpf_skb_load_bytes(skb, offset, &ip_packet, sizeof(ip_packet)) < 0)
        return 0;

    pv_info->is_ip = 1;
    pv_info->ip.is_ipv4 = 1;
    pv_info->ip.ipv4.src_ip = ip_packet.saddr;
    pv_info->ip.ipv4.dst_ip = ip_packet.daddr;
    pv_info->protocol = ip_packet.protocol;

    if (ip_packet.protocol == IPPROTO_TCP) parse_v4_tcp_packet(skb, offset + (ip_packet.ihl * 4), pv_info);
    else if (ip_packet.protocol == IPPROTO_UDP) parse_v4_udp_packet(skb, offset + (ip_packet.ihl * 4), pv_info);
    else if (ip_packet.protocol == IPPROTO_ICMP) parse_v4_icmp_packet(skb, offset + (ip_packet.ihl * 4), pv_info);

    return 0;
}