use crate::constants::MAX_PAYLOAD_SIZE;

#[repr(C, packed)]
#[derive(Clone, Copy)]
pub struct PayloadBuffer {
    pub full_size: u64,
    pub sample_size: u64,
    pub sample_data: [u8; MAX_PAYLOAD_SIZE],
}

#[repr(C, packed)]
#[derive(Clone, Copy)]
pub struct PacketViolationInfo {
    pub violated_rule_id: u64,
    pub violation_type: u8,

    pub protocol: u16,
    pub timestamp_ns: u64,
    pub is_connection_establishing: u8,
    pub direction: u8,

    pub process: ProcessInfo,

    pub src_mac: [u8; 6],
    pub dst_mac: [u8; 6],

    pub is_ip: u8,
    pub ip: IpInfo,

    pub payload: PayloadBuffer,
}

#[repr(C, packed)]
#[derive(Clone, Copy)]
pub struct ProcessInfo {
    pub pid: u32,
    pub name: [u8; 16],
}

#[repr(C, packed)]
#[derive(Clone, Copy)]
pub struct IpInfo {
    pub src_port: u16,
    pub dst_port: u16,
    pub is_ipv4: u8,
    _padding: u8,

    pub addr: IpAddress,
}

#[repr(C, packed)]
#[derive(Copy, Clone)]
pub union IpAddress {
    pub ipv4: Ipv4Addr,
    pub ipv6: Ipv6Addr,
}

#[repr(C, packed)]
#[derive(Copy, Clone)]
pub struct Ipv4Addr {
    pub src_ip: u32,
    pub dst_ip: u32,
}

#[repr(C, packed)]
#[derive(Copy, Clone)]
pub struct Ipv6Addr {
    pub src_ip: [u64; 2],
    pub dst_ip: [u64; 2],
}
