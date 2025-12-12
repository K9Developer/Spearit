#pragma once

#include "vmlinux.h"
#include "types.h"
#include "rule.h"
#include "bpf/bpf_helpers.h"
#include "bpf/bpf_tracing.h"

static __noinline __u64 extract_condition_value_raw(__u8 out[MAX_CONDITION_RAW_VALUE_LENGTH], ConditionValue *cv, PacketViolationInfo *pv_info) {
    if (!cv || !out) return 0;
    if (cv->raw_length == 0 || cv->raw_length > MAX_CONDITION_RAW_VALUE_LENGTH) { // key
        switch (cv->key) {
            case Packet_Length:
                return u64_to_bytes(pv_info->payload.sample_size, out);
            case Packet_SrcIP:
                if (pv_info->ip.is_ipv4)
                    return u64_to_bytes((__u64)pv_info->ip.ipv4.src_ip, out);
                else
                    return u64_pair_to_bytes(pv_info->ip.ipv6.src_ip[0], pv_info->ip.ipv6.src_ip[1], out);
            case Packet_DstIP:
                if (pv_info->ip.is_ipv4)
                    return u64_to_bytes((__u64)pv_info->ip.ipv4.dst_ip, out);
                else
                    return u64_pair_to_bytes(pv_info->ip.ipv6.dst_ip[0], pv_info->ip.ipv6.dst_ip[1], out);
            case Packet_SrcPort:
                return u16_to_bytes(pv_info->ip.src_port, out);
            case Packet_DstPort:
                return u16_to_bytes(pv_info->ip.dst_port, out);
            case Packet_Protocol:
                return u16_to_bytes(pv_info->protocol, out);
            case Packet_Payload:
                return u64_to_bytes(pv_info->payload.sample_size, out);
            default:
                return 0;
        }
    } else { // raw value
        __u32 copy_len = (__u32)cv->raw_length;
        copy_len &= MAX_CONDITION_RAW_VALUE_LENGTH;
        
        bpf_probe_read_kernel(out, copy_len, cv->raw);
        return copy_len;
    }
}

static __noinline bool evaluate_op_num(__u128 val1, Operator op, __u128 val2) {
    switch (op) {
        case Equals:
            return val1 == val2;
        case NotEquals:
            return val1 != val2;
        case LowerThan:
            return val1 < val2;
        case GreaterThan:
            return val1 > val2;
        case LowerThanOrEqual:
            return val1 <= val2;
        case GreaterThanOrEqual:
            return val1 >= val2;
        default:
            return false;
    }
}

static __noinline bool packet_matches_event(EventType event, PacketViolationInfo *pv_info) {
    if (event > Network_CreateConnection) return false;  // not a network event - should not occur as loader should prevent this
    switch (event) {
        case Network_SendPacket:
            return pv_info->direction == DIRECTION_OUTBOUND;
        case Network_ReceivePacket:
            return pv_info->direction == DIRECTION_INBOUND;
        case Network_ReceiveConnection:
            return pv_info->direction == DIRECTION_INBOUND && pv_info->is_connection_establishing;
        case Network_CreateConnection:
            return pv_info->direction == DIRECTION_OUTBOUND && pv_info->is_connection_establishing;
        default:
            return false;
    }
}

__noinline bool has_packet_condition_resolved(PacketViolationInfo *pv_info, Condition *condition) {
    if (!pv_info || !condition) return false;

    // if position in payload is not specified
    if (condition->op == InPayloadAt && condition->value.raw_length == 0) return false;

    // if key requires IP info but packet is not IP
    if (condition->key.raw_length == 0 && (condition->key.key >= 6 && condition->key.key <= 9) && !pv_info->is_ip) return false;

    // if op is payload "contains" nothing - ignore
    if (condition->value.raw_length == 0 && condition->value.key == Packet_Payload) return false;

    // if key is payload but op is not contains
    if (condition->key.raw_length == 0 && condition->key.key == Packet_Payload && condition->op != Contains) return false; 

    // if op is contains but key is not payload
    if (condition->op == Contains && (condition->key.raw_length != 0 || condition->key.key != Packet_Payload)) return false;

    __u8 raw_value1[MAX_CONDITION_RAW_VALUE_LENGTH];
    __u8 raw_value2[MAX_CONDITION_RAW_VALUE_LENGTH];

    // check payload contains condition first
    if (condition->key.raw_length == 0 && condition->key.key == Packet_Payload) {
        __u64 len = extract_condition_value_raw(raw_value2, &condition->value, pv_info);
        // return does_payload_contain(&pv_info->payload, raw_value2, len);
        return false; // TODO: contains is not supported in eBPF currently
    } else if (condition->op == InPayloadAt) {
        __u64 len_key = extract_condition_value_raw(raw_value1, &condition->key, pv_info); // data to check
        __u64 position = condition_value_to_u64(&condition->value); // position in payload
        if (position >= pv_info->payload.sample_size) return false; // value length exceeds payload size
        return is_n_at_x_in_payload(&pv_info->payload, raw_value1[0], position);
    }

    // compare keys to keys
    if (condition->key.raw_length == 0 && condition->value.raw_length == 0) {
        if (condition->key.key == Packet_SrcIP && condition->value.key == Packet_DstIP) {
                if (pv_info->ip.is_ipv4) return pv_info->ip.ipv4.src_ip == pv_info->ip.ipv4.dst_ip;
                else return (pv_info->ip.ipv6.src_ip[0] == pv_info->ip.ipv6.dst_ip[0]) && (pv_info->ip.ipv6.src_ip[1] == pv_info->ip.ipv6.dst_ip[1]);
        }
        if (condition->key.key == Packet_DstIP && condition->value.key == Packet_SrcIP) {
                if (pv_info->ip.is_ipv4) return pv_info->ip.ipv4.dst_ip == pv_info->ip.ipv4.src_ip;
                else return (pv_info->ip.ipv6.dst_ip[0] == pv_info->ip.ipv6.src_ip[0]) && (pv_info->ip.ipv6.dst_ip[1] == pv_info->ip.ipv6.src_ip[1]);
        }
        if (condition->key.key == Packet_SrcPort && condition->value.key == Packet_DstPort) return pv_info->ip.src_port == pv_info->ip.dst_port;
        if (condition->key.key == Packet_DstPort && condition->value.key == Packet_SrcPort) return pv_info->ip.dst_port == pv_info->ip.src_port;
        return false; // even if they are equal its a mistake to compare non matching keys
    }

    switch (condition->key.key) {
        case Packet_Length:
            return evaluate_op_num((__u128)pv_info->payload.sample_size, condition->op, (__u128)*(u64*)condition->value.raw);
        case Packet_SrcIP:
                if (pv_info->ip.is_ipv4) {
                    __u32 val2 = *((__u32*)condition->value.raw);
                    return evaluate_op_num((__u128)pv_info->ip.ipv4.src_ip, condition->op, (__u128)val2);
                } else {
                    __u64 val2_high = *((__u64*)(condition->value.raw + 0));
                    __u64 val2_low  = *((__u64*)(condition->value.raw + 8));
                    __u128 val2 = ((__u128)val2_high << 64) | (__u128)val2_low;
                    __u128 src_ip = ((__u128)pv_info->ip.ipv6.src_ip[1] << 64) | (__u128)pv_info->ip.ipv6.src_ip[0];
                    return evaluate_op_num(src_ip, condition->op, val2);
                }
        case Packet_DstIP:
                if (pv_info->ip.is_ipv4) {
                    __u32 val2 = *((__u32*)condition->value.raw);
                    return evaluate_op_num((__u128)pv_info->ip.ipv4.dst_ip, condition->op, (__u128)val2);
                } else {
                    __u64 val2_high = *((__u64*)(condition->value.raw + 0));
                    __u64 val2_low  = *((__u64*)(condition->value.raw + 8));
                    __u128 val2 = ((__u128)val2_high << 64) | (__u128)val2_low;
                    __u128 dst_ip = ((__u128)pv_info->ip.ipv6.dst_ip[1] << 64) | (__u128)pv_info->ip.ipv6.dst_ip[0];
                    return evaluate_op_num(dst_ip, condition->op, val2);
                }
        case Packet_SrcPort:
            return evaluate_op_num((__u128)pv_info->ip.src_port, condition->op, (__u128)*(u16*)condition->value.raw);
        case Packet_DstPort:
            return evaluate_op_num((__u128)pv_info->ip.dst_port, condition->op, (__u128)*(u16*)condition->value.raw);
        case Packet_Protocol:
            return evaluate_op_num((__u128)pv_info->protocol, condition->op, (__u128)*(u16*)condition->value.raw);
        default:
            return false;
    }

}

// return violated rule id && violated rule order
static __u128 evaluate_packet_rules(void* rules_array_map, PacketViolationInfo *pv_info, bool *has_violation) { 
    if (!has_violation) return 0;
    *has_violation = false;
    if (!rules_array_map || !pv_info) return 0;

    #pragma clang loop unroll(disable)
    for (int rule_ind = 0; rule_ind < MAX_RULES; rule_ind++) {
        CompiledRule *rule = (CompiledRule *)bpf_map_lookup_elem(rules_array_map, &rule_ind);
        if (!rule || rule->conditions.length == 0 || rule->id == 0) continue;

        EventType* events = rule->event_types;
        bool rule_violated = true;
        
        // check if rule events match packet event
        bool found_one_match = false;
        for (int i = 0; i < MAX_EVENTS_PER_RULE; i++) {
            EventType ev = events[i];
            if (events[i] == Event_None) break;
            if (ev == Event_None) break;
            if (packet_matches_event(events[i], pv_info)) {
                found_one_match = true;
                break;
            }
        }
        if (!found_one_match) continue;

        #pragma clang loop unroll(disable)
        for (int cond_ind = 0; cond_ind < MAX_CONDITIONS; cond_ind++) {
            if (cond_ind >= rule->conditions.length) break;
            
            if (!has_packet_condition_resolved(pv_info, &rule->conditions.conditions[cond_ind])) {
                rule_violated = false;
                break;
            }
        }
        if (rule_violated) {
            *has_violation = true;
            return ((__u128)rule->id << (sizeof(__u64) * 8)) | (__u128)rule->order;
        }
    }
    return 0;
}

static __always_inline unsigned int packet_response(__u64 violated_rule_order, void* rules_array_map) {
    if (!rules_array_map) return 0;
    CompiledRule* rule = (CompiledRule*)bpf_map_lookup_elem(rules_array_map, &violated_rule_order);
    if (!rule) return 0;

    ResponseType most_dramatic_response = Alert;
    for (int ri = 0; ri < rule->responses.length; ri++) {
        if (ri >= MAX_RESPONSES) break;
        Response* response = &rule->responses.responses[ri];
        if (!response) continue;
        if (response->type < most_dramatic_response) {
            most_dramatic_response = response->type;
        }
    }
    return (unsigned int)most_dramatic_response;
}