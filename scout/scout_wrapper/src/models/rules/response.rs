use crate::constants::MAX_RESPONSES;

#[repr(C)]
#[derive(Clone, Copy)]
pub enum ResponseType {
    AirGap = 0,
    Kill = 1,
    Isolate = 2,
    Alert = 3,
    Run = 4,
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
pub struct ResponseList {
    pub responses: [Response; MAX_RESPONSES],
    pub length: usize,
}
