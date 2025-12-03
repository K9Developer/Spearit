pub const SOCKET_FIELD_LENGTH_SIZE: usize = 4;
pub const SOCKET_FULL_LENGTH_SIZE: usize = 8;

pub const WRAPPER_SHM_KEY: usize = 0xDEADBEEFDEADBEEF;

// Rules
pub const MAX_CONDITION_RAW_VALUE_LENGTH: usize = 32;
pub const MAX_CONDITIONS: usize = 8; // per rule
pub const MAX_RULES: usize = 64;
pub const MAX_RESPONSES: usize = 5;

enum ViolationType {
    Packet = 0,
    Connection = 1,
}

// Shared Mem
pub const MAX_SHARED_DATA_SIZE: usize = 1024;
pub const SHARED_DATA_LENGTH_SIZE: usize = 8;
pub const REQUEST_ID_SIZE: usize = 4;

pub const MAX_PAYLOAD_SIZE: usize = 128;
