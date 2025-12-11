use once_cell::sync::Lazy;
use ratatui::text::Line;
use std::sync::Mutex;

pub struct ConsoleApp {
    pub current_tab: usize,
    pub wrapper: Vec<Line<'static>>,
    pub loader: Vec<Line<'static>>,
    pub scroll: [u16; term::NUM_TABS],
    pub auto: [bool; term::NUM_TABS],
    pub viewport: u16,
    pub debug: bool,
}

pub struct ScoutWrapperState {
    pub terminal: ConsoleApp,
    pub is_running: bool,
}

impl ScoutWrapperState {
    fn new() -> Self {
        ScoutWrapperState {
            terminal: ConsoleApp {
                current_tab: 0,
                wrapper: vec![],
                loader: vec![],
                scroll: [0; term::NUM_TABS],
                auto: [true; term::NUM_TABS],
                viewport: 0,
                debug: true,
            },
            is_running: true,
        }
    }
}

pub static GLOBAL_STATE: Lazy<Mutex<ScoutWrapperState>> =
    Lazy::new(|| Mutex::new(ScoutWrapperState::new()));

pub const SOCKET_FIELD_LENGTH_SIZE: usize = 4;
pub const SOCKET_FULL_LENGTH_SIZE: usize = 8;

pub const WRAPPER_SHM_KEY: usize = 0xDEADBEEFC0DEFACE;
pub const LOADER_SHM_KEY: usize = 0xCAFEBABEFACEFEED;

// Rules
pub const MAX_CONDITION_RAW_VALUE_LENGTH: usize = 32;
pub const MAX_CONDITIONS: usize = 8; // per rule
pub const MAX_RULES: usize = 64;
pub const MAX_RESPONSES: usize = 5;
pub const MAX_EVENTS_PER_RULE: usize = 5;

enum ViolationType {
    Packet = 0,
    Connection = 1,
}

// Shared Mem
pub const MAX_SHARED_DATA_SIZE: usize = 4096;
pub const SHARED_DATA_LENGTH_SIZE: usize = 8;
pub const REQUEST_ID_SIZE: usize = 4;
pub const SHARED_MEMORY_PATH_WRAPPER: &'static str = "scout_shared_memory_wrapper_write";
pub const SHARED_MEMORY_PATH_LOADER: &'static str = "scout_shared_memory_loader_write";

pub const MAX_PAYLOAD_SIZE: usize = 128;

// Ratatui
pub mod term {
    use ratatui::style::Color;
    pub const NUM_TABS: usize = 2;
    pub const TAB_NORMAL: Color = Color::Rgb(180, 180, 180);
    pub const TAB_SELECTED: Color = Color::Rgb(100, 200, 255);
    pub const TAB_BG: Color = Color::Rgb(40, 50, 60);
    pub const BORDER: Color = Color::Rgb(80, 80, 80);
    pub const TITLE: Color = Color::White;
    pub const HELP_KEY: Color = Color::Rgb(100, 200, 255);
    pub const HELP_TEXT: Color = Color::Rgb(180, 180, 180);
    pub const SCROLL_TRACK: Color = Color::Rgb(60, 60, 60);
    pub const SCROLL_THUMB: Color = Color::Rgb(120, 140, 160);
    pub const AUTO_COLOR: Color = Color::Rgb(100, 200, 100);
}
