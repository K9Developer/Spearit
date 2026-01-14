use getifaddrs::{InterfaceFlags, getifaddrs};
use scout_wrapper::constants::GLOBAL_STATE;
use scout_wrapper::models::connection::connection::Connection;
use scout_wrapper::models::connection::message_trait::MessageTrait;
use scout_wrapper::models::connection::messages::handshake::HandshakeMessage;
use scout_wrapper::models::heartbeat::heartbeat::{Heartbeat, NetworkDetails};
use scout_wrapper::models::logger::logger::set_debug_enabled;
use scout_wrapper::scout_wrapper::ScoutWrapper;
use scout_wrapper::{log_debug, log_error, log_info, log_warn};
use std::collections::HashMap;
use std::net::IpAddr;

fn main() {
    set_debug_enabled(true);
    let mut scout_wrapper = ScoutWrapper::new("10.100.102.169:12345");

    scout_wrapper.launch_ebpf(&std::path::PathBuf::from(
        "/home/k9dev/Coding/Products/Spearit/scout/ebpf/build/loader_spearit",
    ));
    scout_wrapper.connect_shm();

    loop {
        if (!GLOBAL_STATE.lock().unwrap().is_running) {
            log_warn!("Main loop detected shutdown signal. Exiting...");
            break;
        }
        scout_wrapper.loader_handler_tick();
        std::thread::sleep(std::time::Duration::from_millis(100));
    }

    // scout_wrapper.shutdown_ebpf();
}
/*

enum {
    IPPROTO_IP = 0,
    IPPROTO_ICMP = 1,
    IPPROTO_IGMP = 2,
    IPPROTO_IPIP = 4,
    IPPROTO_TCP = 6,
    IPPROTO_EGP = 8,
    IPPROTO_PUP = 12,
    IPPROTO_UDP = 17,
    IPPROTO_IDP = 22,
    IPPROTO_TP = 29,
    IPPROTO_DCCP = 33,
    IPPROTO_IPV6 = 41,
    IPPROTO_RSVP = 46,
    IPPROTO_GRE = 47,
    IPPROTO_ESP = 50,
    IPPROTO_AH = 51,
    IPPROTO_MTP = 92,
    IPPROTO_BEETPH = 94,
    IPPROTO_ENCAP = 98,
    IPPROTO_PIM = 103,
    IPPROTO_COMP = 108,
    IPPROTO_L2TP = 115,
    IPPROTO_SCTP = 132,
    IPPROTO_UDPLITE = 136,
    IPPROTO_MPLS = 137,
    IPPROTO_ETHERNET = 143,
    IPPROTO_AGGFRAG = 144,
    IPPROTO_RAW = 255,
    IPPROTO_SMC = 256,
    IPPROTO_MPTCP = 262,
    IPPROTO_MAX = 263,
};
*/
