use crate::constants::{MAX_CONDITIONS, MAX_CONDITION_RAW_VALUE_LENGTH};
use crate::models::rules::condition::{Condition, ConditionList, ConditionValue, Operator};
use crate::models::rules::dynamic::data_key::ConditionKey;
use crate::models::rules::dynamic::event_type::EventType;
use crate::models::rules::response::Response;

// TODO: Add compiled rule that will only be the rule itself (no extras)

struct Rule {
    id: usize,
    name: String,
    enabled: bool,
    priority: u8,
    event_type: EventType,
    conditions: Vec<Condition>,
    responses: Vec<Response>
}

#[repr(C)]
struct CompiledRule {
    id: usize,
    event_type: EventType,
    conditions: ConditionList,
}

impl Rule {
    pub fn compile(&self) -> CompiledRule {
        let mut conds = ConditionList {
            conditions: [
                Condition {
                    key: ConditionValue { is_key: false, key: ConditionKey::None, raw: [0; MAX_CONDITION_RAW_VALUE_LENGTH] },
                    op: Operator::Equals,
                    value: ConditionValue { is_key: false, key: ConditionKey::None, raw: [0; MAX_CONDITION_RAW_VALUE_LENGTH] },
                }; MAX_CONDITIONS
            ],
            length: 0,
        };
        let count = self.conditions.len().min(MAX_CONDITIONS);
        for (i, cond) in self.conditions.iter().take(count).enumerate() {
            conds.conditions[i] = cond.clone();
        }

        CompiledRule {
            id: self.id,
            event_type: self.event_type,
            conditions: conds
        }
    }
}

struct RuleBuilder {
    curr: Rule
}

impl RuleBuilder {
    pub fn new() -> Self {
        RuleBuilder {
            curr: Rule {
                id: 0,
                name: "".to_string(),
                enabled: false,
                priority: 0,
                event_type: EventType::None,
                conditions: vec![],
                responses: vec![],
            }
        }
    }

    pub fn enabled(mut self) -> Self {
        self.curr.enabled = true;
        self
    }

    pub fn with_priority(mut self, priority: u8) -> Self {
        self.curr.priority = priority;
        self
    }

    pub fn with_event_type(mut self, event_type: EventType) -> Self {
        self.curr.event_type = event_type;
        self
    }

    pub fn with_condition(mut self, condition: Condition) -> Self {
        self.curr.conditions.push(condition);
        self
    }

    pub fn with_response(mut self, response: Response) -> Self {
        self.curr.responses.push(response);
        self
    }

    pub fn build(self) -> Rule {
        self.curr
    }
}