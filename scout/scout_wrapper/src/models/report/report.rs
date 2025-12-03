use crate::models::types::PacketViolationInfo;

enum ReportType {
    ReportPacket = 0,
    ReportFile = 1
}

union ReportData {
    packet_report: PacketViolationInfo
}

#[repr(C)]
pub struct Report {
    pub type_: ReportType,
    pub data: ReportData
}
