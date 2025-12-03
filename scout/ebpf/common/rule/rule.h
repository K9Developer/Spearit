#pragma once

#include "event_type.h"
#include "condition.h"
#include "response.h"

/**
 * CompiledRule represents a rule with its ID, order, event type,
 * conditions to evaluate, and responses to take upon violation.
 * id - Unique identifier for the rule.
 * order - The order of the rule for evaluation priority.
 * event_type - The type of event this rule applies to.
 * conditions - A list of conditions that must be met for the rule to be violated.
 * responses - A list of responses to execute when the rule is violated.
 */
typedef struct {
    unsigned long long id;
    unsigned long long order;
    EventType event_type;
    ConditionList conditions;
    ResponseList responses;
} CompiledRule;