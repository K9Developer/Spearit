use getifaddrs::{InterfaceFlags, getifaddrs};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

fn get_active_ip_and_mac() -> (Option<String>, Option<String>) {
    let mut interfaces = HashMap::new();

    for iface in getifaddrs().unwrap() {
        let entry = interfaces.entry(iface.name.clone()).or_insert((
            None::<std::net::Ipv4Addr>,
            None::<[u8; 6]>,
            iface.flags,
        ));
        if let Some(std::net::IpAddr::V4(ip)) = iface.address.ip_addr() {
            entry.0 = Some(ip);
        }
        if let Some(mac) = iface.address.mac_addr() {
            entry.1 = Some(mac);
        }
    }

    for (name, (ip, mac, flags)) in interfaces {
        if !flags.contains(InterfaceFlags::UP)
            || !flags.contains(InterfaceFlags::RUNNING)
            || flags.contains(InterfaceFlags::LOOPBACK)
        {
            continue;
        }

        if let Some(ip) = ip {
            if ip.is_link_local() {
                continue;
            }

            let ip_str = ip.to_string();
            let mac_str = mac.map(|m| {
                m.iter()
                    .map(|b| format!("{:02x}", b))
                    .collect::<Vec<_>>()
                    .join(":")
            });

            return (Some(ip_str), mac_str);
        }
    }

    (None, None)
}

#[derive(Serialize, Deserialize, Debug)]
pub struct NetworkDetails {
    pub contacted_macs: HashMap<String, i32>, // how many times each MAC was contacted
    pub program_usage: HashMap<String, i32>,  // how many times each program accessed the network
}

#[derive(Serialize, Deserialize, Debug)]
pub struct Heartbeat {
    pub device_name: String,
    pub os_details: String,
    pub ip_address: String,
    pub mac_address: String,
    pub network_details: NetworkDetails,
}

impl Heartbeat {
    pub fn new(
        device_name: String,
        os_details: String,
        ip_address: String,
        mac_address: String,
        network_details: NetworkDetails,
    ) -> Self {
        Heartbeat {
            device_name,
            os_details,
            ip_address,
            mac_address,
            network_details,
        }
    }

    pub fn generate(network_details: NetworkDetails) -> Self {
        let device_name = whoami::devicename();
        let os_details = format!("{} {}", whoami::platform(), whoami::distro());
        let (ip_address, mac_address) = get_active_ip_and_mac();
        Heartbeat {
            device_name,
            os_details,
            ip_address: ip_address.unwrap_or("0.0.0.0".to_string()),
            mac_address: mac_address.unwrap_or("00:00:00:00:00:00".to_string()),
            network_details,
        }
    }

    pub fn to_json(&self) -> String {
        serde_json::to_string(self).unwrap()
    }
}

impl NetworkDetails {
    pub fn new() -> Self {
        NetworkDetails {
            contacted_macs: HashMap::new(),
            program_usage: HashMap::new(),
        }
    }
}
