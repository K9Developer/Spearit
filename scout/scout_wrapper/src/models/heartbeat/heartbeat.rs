use crate::models::shared_types::network_info::NetworkInfo;
use crate::{constants::SYSTEM_METRICS_INTERVAL, log_warn};
use getifaddrs::{InterfaceFlags, getifaddrs};
use serde::Serialize;
use std::collections::HashMap;
use sysinfo::System;

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

#[derive(Serialize, Debug)]
pub struct NetworkDetails {
    pub contacted_macs: HashMap<String, i32>, // how many times each MAC was contacted
}

#[derive(Serialize, Debug)]
pub struct SystemMetrics {
    pub cpu_usage_percent: f32,
    pub memory_usage_percent: f32,

    #[serde(skip_serializing)]
    pub last_updated: u64,
    #[serde(skip_serializing)]
    pub cpu_usage_sample_count: u32,
    #[serde(skip_serializing)]
    pub memory_usage_sample_count: u32,
    #[serde(skip_serializing)]
    pub system: System,
}

#[derive(Serialize, Debug)]
pub struct Heartbeat {
    pub device_name: String,
    pub os_details: String,
    pub ip_address: String,
    pub mac_address: String,
    pub network_details: NetworkDetails,
    pub system_metrics: SystemMetrics,
}

impl Heartbeat {
    pub fn new(
        device_name: String,
        os_details: String,
        ip_address: String,
        mac_address: String,
        network_details: NetworkDetails,
        system_metrics: SystemMetrics,
    ) -> Self {
        Heartbeat {
            device_name,
            os_details,
            ip_address,
            mac_address,
            network_details,
            system_metrics,
        }
    }

    pub fn generate(network_details: NetworkDetails, system_metrics: SystemMetrics) -> Self {
        let device_name = System::host_name().unwrap_or("Unknown Device".to_string());
        let os_details = format!(
            "{} {}",
            System::name().unwrap_or("Unknown OS".to_string()),
            System::os_version().unwrap_or("Unknown Version".to_string())
        );
        let (ip_address, mac_address) = get_active_ip_and_mac();
        Heartbeat {
            device_name,
            os_details,
            ip_address: ip_address.unwrap_or("0.0.0.0".to_string()),
            mac_address: mac_address.unwrap_or("00:00:00:00:00:00".to_string()),
            network_details,
            system_metrics,
        }
    }

    pub fn generate_self(&mut self) {
        let device_name = System::host_name().unwrap_or("Unknown Device".to_string());
        let os_details = format!(
            "{} {}",
            System::name().unwrap_or("Unknown OS".to_string()),
            System::os_version().unwrap_or("Unknown Version".to_string())
        );
        let (ip_address, mac_address) = get_active_ip_and_mac();
        self.device_name = device_name;
        self.os_details = os_details;
        self.ip_address = ip_address.unwrap_or("0.0.0.0".to_string());
        self.mac_address = mac_address.unwrap_or("00:00:00:00:00:00".to_string());
    }

    pub fn reset(&mut self) {
        self.network_details.contacted_macs.clear();
        self.system_metrics.reset();
        self.ip_address = "0.0.0.0".to_string();
        self.mac_address = "00:00:00:00:00:00".to_string();
        self.os_details = "Unknown OS Unknown Version".to_string();
        self.device_name = "Unknown Device".to_string();
    }

    pub fn to_json(&self) -> String {
        serde_json::to_string(self).unwrap()
    }
}

impl NetworkDetails {
    pub fn new() -> Self {
        NetworkDetails {
            contacted_macs: HashMap::new(),
        }
    }

    pub fn merge_network_info(&mut self, network_info: &NetworkInfo) {
        for i in 0..network_info.mac_contacts.current_size as usize {
            let name_bytes = &network_info.mac_contacts.names[i];
            let name_end = name_bytes
                .iter()
                .position(|&b| b == 0)
                .unwrap_or(name_bytes.len());
            let name = String::from_utf8_lossy(&name_bytes[..name_end]).to_string();
            let count = network_info.mac_contacts.counts[i] as i32;
            *self.contacted_macs.entry(name).or_insert(0) += count;
        }
    }
}

impl SystemMetrics {
    pub fn new() -> Self {
        SystemMetrics {
            cpu_usage_percent: 0.0,
            memory_usage_percent: 0.0,
            last_updated: 0,

            cpu_usage_sample_count: 0,
            memory_usage_sample_count: 0,

            system: System::new(),
        }
    }

    pub fn reset(&mut self) {
        self.cpu_usage_percent = 0.0;
        self.memory_usage_percent = 0.0;
        self.cpu_usage_sample_count = 0;
        self.memory_usage_sample_count = 0;
        self.last_updated = 0;
    }

    pub fn update(&mut self) -> Result<(), ()> {
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs();
        let diff = now - self.last_updated;
        if diff >= SYSTEM_METRICS_INTERVAL {
            self.system.refresh_cpu_usage();
            self.system.refresh_memory();
            let cpu = self.system.global_cpu_usage();

            let total_memory = self.system.total_memory() as f32;
            if total_memory <= 0.0 {
                return Err(());
            }
            let used_memory = self.system.used_memory() as f32;
            let memory_usage = (used_memory / total_memory) * 100.0;

            self.cpu_usage_percent = (self.cpu_usage_percent * self.cpu_usage_sample_count as f32
                + cpu)
                / (self.cpu_usage_sample_count as f32 + 1.0);
            self.memory_usage_percent =
                (self.memory_usage_percent * self.memory_usage_sample_count as f32 + memory_usage)
                    / (self.memory_usage_sample_count as f32 + 1.0);
            self.cpu_usage_sample_count += 1;
            self.memory_usage_sample_count += 1;
            self.last_updated = now;
        }
        Ok(())
    }
}
