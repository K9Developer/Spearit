use std::path::{Path, PathBuf};

use crate::{
    log_debug, log_error, log_info,
    models::{
        connection::connection::Connection,
        loader_shm::shared_memory::SharedMemoryManager,
        rules::rule::{RawRule, Rule},
    },
};

// TODO: [8 bytes to signify full message length]
// [4 bytes to signify the goal of the message]
// [4 bytes to signify field 1 length]
// [x bytes for field 1]
// [4 bytes to signify field 2 length]
// [x bytes for field 2]
// TODO: In rule have order and ID, also have type (FROM_AIRGAP, USER, SYSTEM)

enum ScoutWrapperState {
    NotConnected,
    Connected,
}

pub struct ScoutWrapper {
    spear_head_conn: Connection,
    state: ScoutWrapperState,
    loader_conn: SharedMemoryManager,

    rules: Vec<Rule>,
}

impl ScoutWrapper {
    fn load_rules(json_file: PathBuf) -> Vec<Rule> {
        log_debug!("Loading rules from {:?}", json_file);
        let start = std::time::Instant::now();
        let file = std::fs::File::open(json_file).unwrap();
        let raw_rules: Vec<RawRule> = serde_json::from_reader(file).unwrap();
        let mut rules = vec![];
        for raw_rule in raw_rules {
            let rule = raw_rule.compile();
            rules.push(rule);
        }
        log_debug!(
            "Loaded {} rule(s) in {:.2} ms",
            rules.len(),
            start.elapsed().as_secs_f64() * 1000.0
        );
        rules
    }

    pub fn new() -> ScoutWrapper {
        ScoutWrapper {
            spear_head_conn: Connection::new(),
            state: ScoutWrapperState::NotConnected,
            loader_conn: unsafe { SharedMemoryManager::new() },
            rules: ScoutWrapper::load_rules(Path::new("/home/k9dev/Coding/Products/Spearit/scout/scout_wrapper/src/dynamic/rules.json").to_path_buf()),
        }
    }

    pub fn print_rules(&self) {
        for rule in &self.rules {
            log_info!("\tRule ID: {}, Name: {}", rule.id(), rule.name());
        }
    }

    pub fn launch_ebpf(&self, ebpf_path: &PathBuf) {
        log_info!("Launching eBPF module...");

        let child = std::process::Command::new("sudo")
            .arg(ebpf_path)
            .current_dir(ebpf_path.parent().unwrap())
            .spawn();

        match child {
            Ok(_child) => {
                log_info!("eBPF module launched in background.");
            }
            Err(e) => {
                log_error!("Failed to launch eBPF module. Error: {:?}", e);
            }
        }
    }

    pub fn connect_shm_TMP(&mut self) {
        unsafe {
            self.loader_conn.connect();
        }
    }
}
