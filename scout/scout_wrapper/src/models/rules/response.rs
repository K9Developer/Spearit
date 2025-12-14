use crate::constants::MAX_RESPONSES;
use bytemuck::{Pod, Zeroable};

// NOTE: repr(u32) to match C enum size (int = 4 bytes)
#[repr(u32)]
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum ResponseType {
    AirGap = 0,
    Kill = 1,
    Isolate = 2,
    Alert = 3,
    Run = 4,
}

impl ResponseType {
    pub fn from_u32(value: u32) -> ResponseType {
        match value {
            0 => ResponseType::AirGap,
            1 => ResponseType::Kill,
            2 => ResponseType::Isolate,
            3 => ResponseType::Alert,
            4 => ResponseType::Run,
            _ => ResponseType::Alert,
        }
    }
}

#[repr(C)]
#[derive(Copy, Clone)]
pub struct Response {
    pub type_: ResponseType,
}

impl Response {
    pub fn from_string(value: &str) -> Response {
        let type_ = match value {
            "airgap" => ResponseType::AirGap,
            "kill" => ResponseType::Kill,
            "isolate" => ResponseType::Isolate,
            "alert" => ResponseType::Alert,
            "run" => ResponseType::Run,
            _ => ResponseType::Alert, // Default to alert if unknown
        };
        Response { type_ }
    }
}

#[repr(C)]
#[derive(Clone, Copy)]
pub struct ResponseList {
    pub responses: [Response; MAX_RESPONSES],
    pub length: u32,
}
