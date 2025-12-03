#pragma once

#include <constants.h>
#include "condition_key.h"

/**
 * Operators to be evaluated against ConditionValues
 * Contains can be used like:
 * key: "Raw Value"
 * op: Contains
 * value: Packet_Payload
 * Or:
 * key: "0x30 0x43"
 * op: AtInPayload
 * value: "0x23"
 */
typedef enum {
    Equals,
    NotEquals,
    LowerThan,
    GreaterThan,
    LowerThanOrEqual,
    GreaterThanOrEqual,
    Contains,
    InPayloadAt
} Operator;

/**
 * ConditionValue could be a key or a raw value like a string.
 * For example, ConditionValue could be a key (with raw_length set to 0)
 * like Packet_Length, or a raw value like "100" with raw_length set to 3. Its used in both key and
 * value in Condition so we can do something like Connection_DstIP == Connection_SrcIP.
 */
typedef struct {
    unsigned long long raw_length;
    char raw[MAX_CONDITION_RAW_VALUE_LENGTH];
    ConditionKey key;
} ConditionValue;

/**
 * Condition is a part of ConditionList which is basically a rule.
 * It can compare two ConditionValues using an Operator.
 */
typedef struct {
    ConditionValue key;
    Operator op;
    ConditionValue value;
} Condition;

/**
 * ConditionList is a list of Conditions that form a rule.
 */
typedef struct {
    Condition conditions[MAX_CONDITIONS];
    unsigned long length; // size_t
} ConditionList;