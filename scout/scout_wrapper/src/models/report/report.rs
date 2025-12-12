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

#[repr(C)]
pub struct Report {
    pub type_: ReportType,
    pub data: ReportData,
}
