use std::sync::atomic::{AtomicBool, Ordering};

pub const RESET: &str = "\x1b[0m";
pub const D_PRE: &str = "\x1b[1;90m[-]\x1b[0m";
pub const D_MSG: &str = "\x1b[90m";
pub const I_PRE: &str = "\x1b[1;36m[*]\x1b[0m";
pub const I_MSG: &str = "\x1b[37m";
pub const W_PRE: &str = "\x1b[1;33m[!]\x1b[0m";
pub const W_MSG: &str = "\x1b[93m";
pub const E_PRE: &str = "\x1b[1;97;41m[ERROR]";

pub static DEBUG_ENABLED: AtomicBool = AtomicBool::new(false);

pub fn set_debug_enabled(enabled: bool) {
    DEBUG_ENABLED.store(enabled, Ordering::Relaxed);
}

#[macro_export]
macro_rules! log_debug {
    ($($arg:tt)*) => {{
        if crate::models::logger::logger::DEBUG_ENABLED
            .load(std::sync::atomic::Ordering::Relaxed)
        {
            println!(
                "{} {}{}{}",
                crate::models::logger::logger::D_PRE,
                crate::models::logger::logger::D_MSG,
                format!($($arg)*),
                crate::models::logger::logger::RESET
            );
        }
    }};
}

#[macro_export]
macro_rules! log_info {
    ($($arg:tt)*) => {{
        println!(
            "{} {}{}{}",
            crate::models::logger::logger::I_PRE,
            crate::models::logger::logger::I_MSG,
            format!($($arg)*),
            crate::models::logger::logger::RESET
        );
    }};
}

#[macro_export]
macro_rules! log_warn {
    ($($arg:tt)*) => {{
        println!(
            "{} {}{}{}",
            crate::models::logger::logger::W_PRE,
            crate::models::logger::logger::W_MSG,
            format!($($arg)*),
            crate::models::logger::logger::RESET
        );
    }};
}

#[macro_export]
macro_rules! log_error {
    ($($arg:tt)*) => {{
        eprintln!(
            "{} {}{}",
            crate::models::logger::logger::E_PRE,
            format!($($arg)*),
            crate::models::logger::logger::RESET
        );
    }};
}
