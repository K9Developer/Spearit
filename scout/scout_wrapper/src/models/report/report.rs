use crate::constants::MAX_REPORT_MESSAGE_SIZE;

#[repr(C)]
pub struct Report {
    violated_rule_id: usize,
    msg: [u8; MAX_REPORT_MESSAGE_SIZE]
}