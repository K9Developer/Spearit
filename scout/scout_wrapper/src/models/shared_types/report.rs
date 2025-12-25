use serde_json::json;

use crate::models::types::PacketViolationInfo;

#[repr(u32)]
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum ReportType {
    ReportNone = 0,
    ReportPacket = 1,
    ReportFile = 2,
}

#[repr(C)]
pub union ReportData {
    pub packet_report: PacketViolationInfo,
}

impl ReportData {
    pub fn to_json(&self, _type: ReportType) -> serde_json::Value {
        unsafe {
            match _type {
                ReportType::ReportPacket => {
                    let info = &self.packet_report;
                    return info.to_json();
                }
                _ => json!({}),
            }
        }
    }
}

#[repr(C)]
pub struct Report {
    pub type_: ReportType,
    pub data: ReportData,
}

impl Report {
    pub fn to_json(&self) -> serde_json::Value {
        let root = json!({
            "type": match self.type_ {
                ReportType::ReportPacket => "packet",
                ReportType::ReportFile => "file",
                _ => "none",
            },
            "data": self.data.to_json(self.type_),
        });
        root
    }
}
