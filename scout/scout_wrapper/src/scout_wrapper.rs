use std::path::{Path, PathBuf};

use crate::{
    constants::GLOBAL_STATE,
    log_bpf, log_debug, log_error, log_info, log_warn,
    models::{
        connection::connection::Connection,
        loader_shm::shared_memory::SharedMemoryManager,
        rules::rule::{RawRule, Rule},
    },
    terminal_ui::start_terminal,
};
use std::io::BufRead;
use std::io::BufReader;
use std::process::{Command, Stdio};
use std::thread;

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
        std::thread::spawn(|| {
            start_terminal();
        });

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

        let mut child = match Command::new("sudo")
            .arg("stdbuf")
            .arg("-oL")
            .arg("-eL") // THIS IS THE KEY
            .arg(ebpf_path)
            .current_dir(ebpf_path.parent().unwrap())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
        {
            Ok(c) => c,
            Err(e) => {
                log_error!("Failed to launch eBPF module. Error: {:?}", e);
                return;
            }
        };

        log_info!("eBPF module launched in background.");

        if let Some(stdout) = child.stdout.take() {
            thread::spawn(move || {
                let reader = std::io::BufReader::new(stdout);
                for line in reader.lines().flatten() {
                    log_bpf!("{}", line);
                }
            });
        }

        if let Some(stderr) = child.stderr.take() {
            thread::spawn(move || {
                let reader = std::io::BufReader::new(stderr);
                for line in reader.lines().flatten() {
                    log_bpf!("{}", line);
                }
            });
        }
    }

    pub fn connect_shm_TMP(&mut self) {
        unsafe {
            self.loader_conn.connect();
        }
    }
}
