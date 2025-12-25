use crate::constants::{MAX_NETWORK_RECORD_NAME_LENGTH, MAX_NETWORK_RECORDS};

#[repr(C)]
#[derive(Debug)]
pub struct NetworkContacts {
    pub names: [[u8; MAX_NETWORK_RECORD_NAME_LENGTH]; MAX_NETWORK_RECORDS],
    pub counts: [u32; MAX_NETWORK_RECORDS],
    pub current_size: u32,
}

#[repr(C)]
#[derive(Debug)]
pub struct NetworkInfo {
    pub mac_contacts: NetworkContacts,
}
