use crate::constants::{
    MAX_CONDITION_RAW_VALUE_LENGTH, MAX_CONDITIONS, MAX_EVENTS_PER_RULE, MAX_RESPONSES,
};
use crate::log_warn;
use crate::models::rules::condition::{
    Condition, ConditionList, ConditionValue, Operator, RawCondition,
};
use crate::models::rules::dynamic::data_key::ConditionKey;
use crate::models::rules::dynamic::event_type::EventType;
use crate::models::rules::response::{Response, ResponseList, ResponseType};
use serde::Deserialize;

// TODO: Add compiled rule that will only be the rule itself (no extras)

// serde deserialized
#[derive(serde::Deserialize)]
pub struct RawRule {
    pub id: usize,
    pub order: usize,
    pub name: String,
    pub enabled: bool,
    pub priority: u8,
    pub event_types: Vec<String>,
    pub conditions: Vec<RawCondition>,
    pub responses: Vec<String>,
}

impl RawRule {
    pub fn compile(self) -> Rule {
        let mut rule = RuleBuilder::new();
        rule = rule.with_id(self.id);
        rule = rule.with_order(self.order);
        rule = rule.with_name(self.name);
        rule = if self.enabled { rule.enabled() } else { rule };
        rule = rule.with_priority(self.priority);

        let mut event_types = [EventType::Event_None; MAX_EVENTS_PER_RULE];
        for (i, et) in self.event_types.iter().enumerate() {
            event_types[i] = EventType::from_string(et);
        }
        rule = rule.with_event_types(event_types);

        for raw_cond in self.conditions {
            rule = rule.with_condition(Condition::from_raw(raw_cond));
        }

        for resp_str in self.responses {
            rule = rule.with_response(Response::from_string(&resp_str));
        }

        rule.build()
    }
}

pub struct Rule {
    id: usize,
    order: usize,
    name: String,
    enabled: bool,
    priority: u8,
    event_types: [EventType; MAX_EVENTS_PER_RULE],
    conditions: Vec<Condition>,
    responses: Vec<Response>,
}

#[repr(C)]
#[derive(Clone, Copy)]
pub struct CompiledRule {
    pub id: usize,
    pub order: usize,
    pub event_types: [EventType; MAX_EVENTS_PER_RULE],
    pub conditions: ConditionList,
    pub responses: ResponseList,
}

impl Rule {
    pub fn compile(&self) -> CompiledRule {
        let mut conds = ConditionList {
            conditions: [Condition {
                key: ConditionValue {
                    raw_length: 0,
                    key: ConditionKey::Condition_None,
                    raw: [0; MAX_CONDITION_RAW_VALUE_LENGTH],
                },
                op: Operator::Equals,
                value: ConditionValue {
                    raw_length: 0,
                    key: ConditionKey::Condition_None,
                    raw: [0; MAX_CONDITION_RAW_VALUE_LENGTH],
                },
            }; MAX_CONDITIONS],
            length: 0,
        };
        let count = self.conditions.len().min(MAX_CONDITIONS);
        for (i, cond) in self.conditions.iter().take(count).enumerate() {
            conds.conditions[i] = cond.clone();
        }
        conds.length = count;

        let mut reses: [Response; MAX_RESPONSES] = [Response {
            type_: ResponseType::Run,
        }; MAX_RESPONSES];
        for (i, v) in self.responses.iter().take(MAX_RESPONSES).enumerate() {
            reses[i] = v.clone();
        }

        CompiledRule {
            id: self.id,
            order: self.order,
            event_types: self.event_types,
            responses: ResponseList {
                responses: reses,
                length: self.responses.len().min(MAX_RESPONSES) as u32,
            },
            conditions: conds,
        }
    }

    pub fn id(&self) -> usize {
        self.id
    }
    pub fn name(&self) -> &str {
        &self.name
    }
    pub fn enabled(&self) -> bool {
        self.enabled
    }
    pub fn priority(&self) -> u8 {
        self.priority
    }
    pub fn event_types(&self) -> &[EventType; MAX_EVENTS_PER_RULE] {
        &self.event_types
    }
    pub fn conditions(&self) -> &Vec<Condition> {
        &self.conditions
    }
    pub fn responses(&self) -> &Vec<Response> {
        &self.responses
    }
    pub fn order(&self) -> usize {
        self.order
    }
}

struct RuleBuilder {
    curr: Rule,
}

impl RuleBuilder {
    pub fn new() -> Self {
        RuleBuilder {
            curr: Rule {
                id: 0,
                order: 0,
                name: "".to_string(),
                enabled: false,
                priority: 0,
                event_types: [EventType::Event_None; MAX_EVENTS_PER_RULE],
                conditions: vec![],
                responses: vec![],
            },
        }
    }

    pub fn with_id(mut self, id: usize) -> Self {
        self.curr.id = id;
        self
    }

    pub fn with_order(mut self, order: usize) -> Self {
        self.curr.order = order;
        self
    }

    pub fn with_name<S: Into<String>>(mut self, name: S) -> Self {
        self.curr.name = name.into();
        self
    }

    pub fn enabled(mut self) -> Self {
        self.curr.enabled = true;
        self
    }

    pub fn with_priority(mut self, priority: u8) -> Self {
        self.curr.priority = priority;
        self
    }

    pub fn with_event_types(mut self, event_types: [EventType; MAX_EVENTS_PER_RULE]) -> Self {
        self.curr.event_types = event_types;
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
