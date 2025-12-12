use std::fmt::Debug;

use crate::{constants::MAX_PAYLOAD_SIZE, log_error};

#[repr(C)]
#[derive(Clone, Copy, Debug)]
pub struct PayloadBuffer {
    pub full_size: u64,
    pub sample_size: u64,
    pub sample_data: [u8; MAX_PAYLOAD_SIZE],
}

#[repr(C)]
#[derive(Clone, Copy)]
pub struct PacketViolationInfo {
    pub violated_rule_id: u64,
    pub violation_type: u8,
    pub violation_response: u32,

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

impl Debug for PacketViolationInfo {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        // --- Copy all fields out of the packed struct ---
        let violated_rule_id = self.violated_rule_id;
        let violation_type = self.violation_type;
        let violation_response = self.violation_response;

        let protocol = self.protocol;
        let timestamp_ns = self.timestamp_ns;
        let is_connection_establishing = self.is_connection_establishing;
        let direction = self.direction;

        let process = self.process;
        let src_mac = self.src_mac;
        let dst_mac = self.dst_mac;

        let is_ip = self.is_ip;
        let ip = self.ip; // IpInfo is Copy
        let payload = self.payload;

        // --- Convert MAC addresses ---
        let format_mac = |mac: [u8; 6]| {
            format!(
                "{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}",
                mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]
            )
        };
        let src_mac_str = format_mac(src_mac);
        let dst_mac_str = format_mac(dst_mac);

        // --- Convert IP info ---
        let mut ip_str = String::new();
        let mut src_port = 0u16;
        let mut dst_port = 0u16;

        if is_ip != 0 {
            src_port = ip.src_port;
            dst_port = ip.dst_port;

            if ip.is_ipv4 != 0 {
                // IPv4: convert integer to dotted notation
                let ipv4 = unsafe { ip.addr.ipv4 };
                let src = ipv4.src_ip.to_be_bytes();
                let dst = ipv4.dst_ip.to_be_bytes();

                ip_str = format!(
                    "IPv4 src={}.{}.{}.{} dst={}.{}.{}.{}",
                    src[0], src[1], src[2], src[3], dst[0], dst[1], dst[2], dst[3],
                );
            } else {
                // IPv6
                let ipv6 = unsafe { ip.addr.ipv6 };
                let src = ipv6.src_ip;
                let dst = ipv6.dst_ip;

                ip_str = format!(
                    "IPv6 src={:x}:{:x}:{:x}:{:x}:{:x}:{:x}:{:x}:{:x} \
                          dst={:x}:{:x}:{:x}:{:x}:{:x}:{:x}:{:x}:{:x}",
                    src[0] >> 48,
                    (src[0] >> 32) & 0xffff,
                    (src[0] >> 16) & 0xffff,
                    src[0] & 0xffff,
                    src[1] >> 48,
                    (src[1] >> 32) & 0xffff,
                    (src[1] >> 16) & 0xffff,
                    src[1] & 0xffff,
                    dst[0] >> 48,
                    (dst[0] >> 32) & 0xffff,
                    (dst[0] >> 16) & 0xffff,
                    dst[0] & 0xffff,
                    dst[1] >> 48,
                    (dst[1] >> 32) & 0xffff,
                    (dst[1] >> 16) & 0xffff,
                    dst[1] & 0xffff,
                );
            }
        }

        // --- Payload formatting ---
        let full_size = payload.full_size;
        let sample_size = payload.sample_size as usize;

        // Hex dump up to sample_size bytes
        let mut hex_dump = String::new();
        let slice = &payload.sample_data[..sample_size.min(payload.sample_data.len())];
        for b in slice {
            use core::fmt::Write;
            let _ = write!(hex_dump, "{:02x} ", b);
        }

        // --- Process name ---
        let process_name = {
            let mut name = String::new();
            for &c in &process.name {
                if c == 0 {
                    break;
                }
                name.push(c as char);
            }
            name
        };
        let process_pid = process.pid;

        // --- Build debug output ---
        let mut ds = f.debug_struct("PacketViolationInfo");

        ds.field("violated_rule_id", &violated_rule_id)
            .field("is_ip", &is_ip)
            .field("violation_type", &violation_type)
            .field("violation_response", &violation_response)
            .field("protocol", &protocol)
            .field("timestamp_ns", &timestamp_ns)
            .field("is_connection_establishing", &is_connection_establishing)
            .field("direction", &direction)
            .field("process_pid", &process_pid)
            .field("process_name", &process_name)
            .field("src_mac", &src_mac_str)
            .field("dst_mac", &dst_mac_str)
            .field("is_ip", &is_ip)
            .field("ip_info", &ip_str)
            .field("src_port", &src_port)
            .field("dst_port", &dst_port)
            .field("payload_full_size", &full_size)
            .field("payload_sample_size", &sample_size)
            .field("payload_hex_dump", &hex_dump);

        ds.finish()
    }
}

#[repr(C)]
#[derive(Clone, Copy, Debug)]
pub struct ProcessInfo {
    pub pid: u32,
    pub name: [u8; 16],
}

#[repr(C)]
#[derive(Clone, Copy, Debug)]
pub struct IpInfo {
    pub src_port: u16,
    pub dst_port: u16,
    pub is_ipv4: u8,

    pub addr: IpAddress,
}

#[repr(C)]
#[derive(Copy, Clone)]
pub union IpAddress {
    pub ipv4: Ipv4Addr,
    pub ipv6: Ipv6Addr,
}

impl Debug for IpAddress {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        unsafe {
            write!(
                f,
                "IpAddress {{ ipv4: {:?}, ipv6: {:?} }}",
                self.ipv4, self.ipv6
            )
        }
    }
}

#[repr(C)]
#[derive(Copy, Clone, Debug)]
pub struct Ipv4Addr {
    pub src_ip: u32,
    pub dst_ip: u32,
}

#[repr(C)]
#[derive(Copy, Clone, Debug)]
pub struct Ipv6Addr {
    pub src_ip: [u64; 2],
    pub dst_ip: [u64; 2],
}
