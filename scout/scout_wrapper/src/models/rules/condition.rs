use crate::constants::{MAX_CONDITION_RAW_VALUE_LENGTH, MAX_CONDITIONS};
use crate::models::rules::dynamic::data_key::ConditionKey;
use base64::prelude::*;
use libc::c_uchar;
use std::ffi::c_char;

#[repr(C)]
#[derive(Clone, Copy)]
pub enum Operator {
    Equals,
    NotEquals,
    LowerThan,
    GreaterThan,
    LowerThanOrEqual,
    GreaterThanOrEqual,
    Inside,
    InPayloadAt,
}

impl Operator {
    pub fn from_string(value: &str) -> Operator {
        match value {
            "equals" => Operator::Equals,
            "not_equals" => Operator::NotEquals,
            "lower_than" => Operator::LowerThan,
            "greater_than" => Operator::GreaterThan,
            "lower_than_or_equal" => Operator::LowerThanOrEqual,
            "greater_than_or_equal" => Operator::GreaterThanOrEqual,
            "inside" => Operator::Inside,
            "in_payload_at" => Operator::InPayloadAt,
            _ => Operator::Equals, // Default to equals if unknown
        }
    }
}

#[repr(C)]
#[derive(Clone, Copy)]
pub struct ConditionValue {
    pub(crate) raw_length: usize,
    pub(crate) raw: [c_uchar; MAX_CONDITION_RAW_VALUE_LENGTH],
    pub(crate) key: ConditionKey,
}

impl ConditionValue {
    pub fn from_raw(raw: RawConditionValue) -> Self {
        if raw.is_key {
            ConditionValue {
                raw_length: 0,
                raw: [0; MAX_CONDITION_RAW_VALUE_LENGTH],
                key: ConditionKey::from_string(&raw.value),
            }
        } else {
            let mut raw_bytes = [0; MAX_CONDITION_RAW_VALUE_LENGTH];
            let b64val = BASE64_STANDARD
                .decode(raw.value.as_bytes())
                .unwrap_or_default();
            let len = b64val.len().min(MAX_CONDITION_RAW_VALUE_LENGTH);
            raw_bytes[..len].copy_from_slice(&b64val[..len]);
            ConditionValue {
                raw_length: len,
                raw: raw_bytes,
                key: ConditionKey::Condition_None,
            }
        }
    }
}

#[repr(C)]
#[derive(Copy, Clone)]
pub struct Condition {
    pub key: ConditionValue,
    pub op: Operator,
    pub value: ConditionValue,
}

impl Condition {
    pub fn from_raw(raw: RawCondition) -> Self {
        let key = ConditionValue::from_raw(raw.key);
        let value = ConditionValue::from_raw(raw.value);
        let op = Operator::from_string(&raw.operator);
        Condition { key, op, value }
    }
}

pub struct ConditionList {
    pub conditions: [Condition; MAX_CONDITIONS],
    pub length: usize,
}

#[derive(serde::Deserialize)]
pub struct RawConditionValue {
    pub is_key: bool,
    pub value: String,
}

#[derive(serde::Deserialize)]
pub struct RawCondition {
    pub key: RawConditionValue,
    pub operator: String,
    pub value: RawConditionValue,
}
