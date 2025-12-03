use std::ffi::c_char;
use crate::constants::{MAX_CONDITIONS, MAX_CONDITION_RAW_VALUE_LENGTH};
use crate::models::rules::dynamic::data_key::ConditionKey;

#[repr(C)]
#[derive(Clone, Copy)]
pub enum Operator {
    Equals,
    NotEquals,
    LowerThan,
    GreaterThan,
    LowerThanOrEqual,
    GreaterThanOrEqual,
    Inside
}

#[repr(C)]
#[derive(Clone, Copy)]
pub struct ConditionValue {
    pub(crate) raw_length: usize,
    pub(crate) raw: [c_char; MAX_CONDITION_RAW_VALUE_LENGTH],
    pub(crate) key: ConditionKey
}

#[repr(C)]
#[derive(Copy, Clone)]
pub struct Condition {
    pub key: ConditionValue,
    pub op: Operator,
    pub value: ConditionValue
}

pub struct ConditionList {
    pub conditions: [Condition; MAX_CONDITIONS],
    pub length: usize
}