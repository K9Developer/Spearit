#pragma once

#include "vmlinux.h"
#include "types.h"
#include "bpf/bpf_helpers.h"
#include <condition.h>

static __noinline int extract_payload(struct __sk_buff *skb, __u32 offset, PayloadBuffer *payload)
{
    if (!skb || !payload)
        return 0;

    __u32 pkt_len = skb->len;

    if (offset >= pkt_len) {
        payload->full_size = 0;
        payload->sample_size = 0;
        return 0;
    }

    __u32 len = pkt_len - offset;
    payload->full_size = len;
    if (len > MAX_PAYLOAD_SIZE)
        len = MAX_PAYLOAD_SIZE;
    payload->sample_size = len;

    #pragma clang loop unroll(disable)
    for (__u32 i = 0; i < MAX_PAYLOAD_SIZE; i++) {
        if (i >= len)
            break;

        __u8 tmp = 0;

        long err = bpf_skb_load_bytes(skb, offset + i, &tmp, 1);
        if (err < 0) {
            bpf_printk("Failed to load skb payload byte at offset %u\n", offset + i);
            break;
        }

        payload->sample_data[i] = tmp;
    }

    return 0;
}

// static __noinline bool does_payload_contain(PayloadBuffer *payload, __u8 pattern[MAX_CONDITION_RAW_VALUE_LENGTH], __u64 pattern_length)
// {
//     if (!payload || !pattern) return false;
//     if (pattern_length == 0 || pattern_length > MAX_CONDITION_RAW_VALUE_LENGTH) return false;

//     __u64 current_pattern_index = 0;

//     #pragma clang loop unroll(disable)
//     for (int i = 0; i < MAX_PAYLOAD_SIZE - MAX_PATTERN; i++) {
//     bool match = true;

//         #pragma clang loop unroll(disable)
//         for (int j = 0; j < MAX_PATTERN; j++) {
//             if (j >= pattern_length) break;
//             if (payload->sample_data[i + j] != pattern[j]) {
//                 match = false;
//                 break;
//             }
//         }

//         if (match) return true;
//     }
//     return false;
// }

static __noinline bool is_n_at_x_in_payload(PayloadBuffer *payload, __u8 byte, __u64 position)
{
    if (!payload) return false;
    if (position + 1 > payload->sample_size) return false;
    if (position >= MAX_PAYLOAD_SIZE) return false;

    unsigned char byte_at_pos = payload->sample_data[position];
    if (byte_at_pos != byte) {
        return false;
    }

    return true;
}

static __noinline __u64 condition_value_to_u64(ConditionValue *cv) {
    if (!cv) return 0;
    return *(__u64*)cv->raw;
}

static __noinline __u64 u16_to_bytes(__u16 value, unsigned char out[MAX_CONDITION_RAW_VALUE_LENGTH]) {   
    out[0] = (__u8)(value >> 0);
    out[1] = (__u8)(value >> 8);
    return sizeof(__u16);
}

static __noinline __u64 u64_to_bytes(__u64 val, __u8 out[MAX_CONDITION_RAW_VALUE_LENGTH])
{
    out[0] = (val >> 0);
    out[1] = (val >> 8);
    out[2] = (val >> 16);
    out[3] = (val >> 24);
    out[4] = (val >> 32);
    out[5] = (val >> 40);
    out[6] = (val >> 48);
    out[7] = (val >> 56);
    return sizeof(__u64);
}

static __noinline __u64 u64_pair_to_bytes(__u64 low, __u64 high, __u8 out[MAX_CONDITION_RAW_VALUE_LENGTH])
{
    out[0] = (__u8)(low >> 0);
    out[1] = (__u8)(low >> 8);
    out[2] = (__u8)(low >> 16);
    out[3] = (__u8)(low >> 24);
    out[4] = (__u8)(low >> 32);
    out[5] = (__u8)(low >> 40);
    out[6] = (__u8)(low >> 48);
    out[7] = (__u8)(low >> 56);
    out[8] = (__u8)(high >> 0);
    out[9] = (__u8)(high >> 8);
    out[10] = (__u8)(high >> 16);
    out[11] = (__u8)(high >> 24);
    out[12] = (__u8)(high >> 32);
    out[13] = (__u8)(high >> 40);
    out[14] = (__u8)(high >> 48);
    out[15] = (__u8)(high >> 56);
    return sizeof(__u64) * 2;
}

static __noinline __u64 u128_to_bytes(__u128 value, char out[MAX_CONDITION_RAW_VALUE_LENGTH]) {
    #pragma clang loop unroll(disable)
    for (int i = 0; i < MAX_CONDITION_RAW_VALUE_LENGTH; i++) {
        out[i] = (value >> (i * 8)) & 0xFF;
    }
    return sizeof(__u128);
}

static __noinline __u64 bytes_to_u64(const __u8 *buf, __u64 len)
{
    __u64 val = 0;

    if (!buf || len == 0 || len > 8)
        return 0;

    // Manual duplication of 8 bytes — verifier loves this
    if (len > 0) val |= (__u64)buf[0];
    if (len > 1) val |= (__u64)buf[1] << 8;
    if (len > 2) val |= (__u64)buf[2] << 16;
    if (len > 3) val |= (__u64)buf[3] << 24;
    if (len > 4) val |= (__u64)buf[4] << 32;
    if (len > 5) val |= (__u64)buf[5] << 40;
    if (len > 6) val |= (__u64)buf[6] << 48;
    if (len > 7) val |= (__u64)buf[7] << 56;

    return val;
}

static __noinline bool are_buffers_equal(__u8* buf1, __u8* buf2, __u64 length1, __u64 length2) {
    if (!buf1 || !buf2) return false;
    if (length1 != length2) return false;
    __u64 len = length1;
    // len is known to be <= 32 from extract_condition_value_raw()
    if (len == 0) return true;

    __u64 diff = 0;

    // Compare up to 8 bytes at a time when possible
    if (len >= 8) {
        __u64 v1 = *(const __u64*)buf1;
        __u64 v2 = *(const __u64*)buf2;
        diff |= (v1 ^ v2);
        if (diff) return false;
        buf1 += 8; buf2 += 8; len -= 8;
    }
    if (len >= 4) {
        __u32 v1 = *(const __u32*)buf1;
        __u32 v2 = *(const __u32*)buf2;
        diff |= (v1 ^ v2);
        if (diff) return false;
        buf1 += 4; buf2 += 4; len -= 4;
    }
    if (len >= 2) {
        __u16 v1 = *(const __u16*)buf1;
        __u16 v2 = *(const __u16*)buf2;
        diff |= (v1 ^ v2);
        if (diff) return false;
        buf1 += 2; buf2 += 2; len -= 2;
    }
    if (len >= 1) {
        diff |= buf1[0] ^ buf2[0];
    }

    return diff == 0;
}

static __noinline bool is_buffer_lower_than(__u8* buf1, __u8* buf2, __u64 length1, __u64 length2) {
    if (!buf1 || !buf2) return false;
    u64 low1 = 0, high1 = 0, low2 = 0, high2 = 0;
    u64 low1off = length1 >= 8 ? 8 : length1;
    u64 low2off = length2 >= 8 ? 8 : length2;
    high1 = bytes_to_u64(buf1 + low1off, length1 - low1off);
    high2 = bytes_to_u64(buf2 + low2off, length2 - low2off); 
    if (high1 < high2) return true;
    if (high1 > high2) return false;
    low1 = bytes_to_u64(buf1, low1off);
    low2 = bytes_to_u64(buf2, low2off);
    return low1 < low2;
}


static __noinline bool is_buffer_greater_than(__u8* buf1, __u8* buf2, __u64 length1, __u64 length2) {
    if (!buf1 || !buf2) return false;
    // struct u128_pair val1;
    // struct u128_pair val2;
    // val1.low = val1.high = val2.low = val2.high = 0;

    // bytes_to_u128(buf1, length1, &val1);
    // bytes_to_u128(buf2, length2, &val2);

    // if (val1.high > val2.high) return true;
    // if (val1.high < val2.high) return false;
    // return val1.low > val2.low;

    u64 low1 = 0, high1 = 0, low2 = 0, high2 = 0;
    u64 low1off = length1 >= 8 ? 8 : length1;
    u64 low2off = length2 >= 8 ? 8 : length2;
    high1 = bytes_to_u64(buf1 + low1off, length1 - low1off);
    high2 = bytes_to_u64(buf2 + low2off, length2 - low2off);
    if (high1 > high2) return true;
    if (high1 < high2) return false;
    low1 = bytes_to_u64(buf1, low1off);
    low2 = bytes_to_u64(buf2, low2off);
    return low1 > low2;
}