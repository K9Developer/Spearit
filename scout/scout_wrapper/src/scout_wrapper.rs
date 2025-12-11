use std::path::{Path, PathBuf};

use crate::{
    constants::GLOBAL_STATE,
    log_bpf, log_debug, log_error, log_info, log_warn,
    models::{
        connection::connection::Connection,
        loader_shm::shared_memory::{CommID, SharedMemoryManager},
        rules::rule::{CompiledRule, RawRule, Rule},
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

    loader_process: Option<std::process::Child>,

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
            loader_process: None,
            rules: ScoutWrapper::load_rules(Path::new("/home/k9dev/Coding/Products/Spearit/scout/scout_wrapper/src/dynamic/rules.json").to_path_buf()),
        }
    }

    pub fn print_rules(&self) {
        for rule in &self.rules {
            log_info!("\tRule ID: {}, Name: {}", rule.id(), rule.name());
        }
    }

    pub fn launch_ebpf(&mut self, ebpf_path: &PathBuf) {
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
        self.loader_process = Some(child);

        log_info!("eBPF module launched in background.");

        if let Some(stdout) = self.loader_process.as_mut().unwrap().stdout.take() {
            thread::spawn(move || {
                let reader = std::io::BufReader::new(stdout);
                for line in reader.lines().flatten() {
                    log_bpf!("{}", line);
                }
            });
        }

        if let Some(stderr) = self.loader_process.as_mut().unwrap().stderr.take() {
            thread::spawn(move || {
                let reader = std::io::BufReader::new(stderr);
                for line in reader.lines().flatten() {
                    log_bpf!("{}", line);
                }
            });
        }
    }

    pub fn loader_handler_tick(&mut self) {
        unsafe {
            let res = self.loader_conn.read(-1);
            if res.is_none() {
                return;
            }
            let res = res.unwrap();
            let req_id = CommID::from_u32(res.request_id);
            match req_id {
                Some(CommID::ReqActiveRuleIds) => {
                    log_debug!("Received active rule IDs request from loader.");
                    let active_rule_ids: Vec<usize> = self
                        .rules
                        .iter()
                        .filter(|r| r.enabled())
                        .map(|r| r.id())
                        .collect();
                    self.loader_conn.write(
                        CommID::ResActiveRuleIds,
                        bytemuck::cast_slice(&active_rule_ids),
                        res.current_conversation_id as i32,
                    );
                }
                Some(CommID::ReqRuleData) => {
                    let requested_rule_id = {
                        let mut buf = [0u8; 8];
                        buf.copy_from_slice(&res.data[0..8]);
                        usize::from_le_bytes(buf)
                    };
                    log_debug!("Loader requested data for rule ID: {}", requested_rule_id);
                    let rule_opt = self.rules.iter().find(|r| r.id() == requested_rule_id);
                    if let Some(rule) = rule_opt {
                        let compiled_rule = rule.compile();
                        let mut data_bytes = vec![0u8; std::mem::size_of::<CompiledRule>()];

                        unsafe {
                            std::ptr::copy_nonoverlapping(
                                &compiled_rule as *const CompiledRule as *const u8,
                                data_bytes.as_mut_ptr(),
                                data_bytes.len(),
                            );
                        }

                        self.loader_conn.write(
                            CommID::ResRuleData,
                            &data_bytes,
                            res.current_conversation_id as i32,
                        );
                    } else {
                        log_warn!("Requested rule ID {} not found.", requested_rule_id);
                        self.loader_conn.write(
                            CommID::ResRuleData,
                            &[],
                            res.current_conversation_id as i32,
                        );
                    }
                }
                _ => {}
            }
        }
    }

    pub fn shutdown_ebpf(&mut self) {
        log_info!("Shutting down eBPF module...");
        if let Some(child) = &mut self.loader_process {
            match child.kill() {
                Ok(_) => log_info!("eBPF module shut down successfully."),
                Err(e) => log_error!("Failed to shut down eBPF module. Error: {:?}", e),
            }
        } else {
            log_warn!("No eBPF module process found to shut down.");
        }
    }

    pub fn connect_shm(&mut self) {
        log_info!("Connecting to loader shared memory...");
        unsafe {
            self.loader_conn.connect();
        }
        log_debug!("Connected to loader shared memory.");
    }
}
