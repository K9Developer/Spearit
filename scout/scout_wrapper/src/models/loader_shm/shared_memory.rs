use std::ffi::{CStr, CString};
use std::{mem, ptr, thread};
use std::mem::offset_of;
use std::ptr::null;
use std::sync::atomic::{AtomicBool, Ordering};
use std::time::Duration;
use libc::{c_int, O_CREAT, O_RDWR, c_char, size_t, PROT_WRITE, PROT_READ, MAP_SHARED, MAP_FAILED, mmap, strerror, perror, ftruncate};
use crate::constants::{MAX_SHARED_DATA_SIZE, SHARED_MEMORY_PATH_LOADER, SHARED_MEMORY_PATH_WRAPPER, WRAPPER_SHM_KEY};

unsafe extern "C" {
    pub fn shm_open(name: *const c_char, oflag: c_int, mode: c_int) -> c_int;
    pub fn shm_unlink(name: *const c_char) -> c_int;
}

#[repr(C)]
#[derive(Debug, Clone, Copy)]
pub enum CommID {
    ReqActiveRuleIds = 0,
    ReqRuleData = 1,
    ResRuleViolation = 2,
    ResActiveRuleIds = 3,
}

impl CommID {
    pub fn from_u32(value: u32) -> Option<Self> {
        match value {
            0 => Some(CommID::ReqActiveRuleIds),
            1 => Some(CommID::ReqRuleData),
            2 => Some(CommID::ResRuleViolation),
            3 => Some(CommID::ResActiveRuleIds),
            _ => None,
        }
    }

    pub fn as_u32(&self) -> u32 {
        *self as u32
    }
}

#[repr(C)]
#[derive(Debug, Copy, Clone)]
pub struct RawCommsResponse {
    pub data: [u8; MAX_SHARED_DATA_SIZE],
    pub size: usize,
    pub current_conversation_id: usize,
    pub request_id: u32, // Using u32 to match typical C enum size
}

impl Default for RawCommsResponse {
    fn default() -> Self {
        Self {
            data: [0u8; MAX_SHARED_DATA_SIZE],
            size: 0,
            current_conversation_id: 0,
            request_id: 0,
        }
    }
}

#[repr(C)]
#[derive(Debug)]
pub struct SharedComms {
    pub key: usize,
    pub ready: AtomicBool,
    pub current_conversation_id: usize,
    pub request_id: u32,
    pub size: usize,
    pub data: [u8; MAX_SHARED_DATA_SIZE],
}

impl SharedComms {
    pub fn new(key: usize) -> Self {
        SharedComms {
            key,
            size: 0,
            ready: AtomicBool::new(false),
            current_conversation_id: 0,
            request_id: 0,
            data: [0u8; MAX_SHARED_DATA_SIZE]
        }
    }
}

pub struct SharedMemoryManager {
    shared_input: *mut SharedComms,
    shared_output: *mut SharedComms,
    last_read_conversation_id: usize,
    last_write_conversation_id: usize,
}

impl SharedMemoryManager {
    unsafe fn create_shm(name: &str) -> *mut SharedComms {
        let name = CString::new(name).unwrap();
        let fd: c_int = shm_open(name.as_ptr(), O_CREAT | O_RDWR, 0600);
        if fd < 0 {
            perror(CString::new("Shared memory opening failed").unwrap().as_ptr());
            panic!("Failed to open shared memory");
        }
        println!("Opened shared memory");
        let size = size_of::<SharedComms>();


        let addr = mmap(
            ptr::null_mut(),
            size as size_t,
            PROT_READ | PROT_WRITE,
            MAP_SHARED,
            fd,
            0,
        );

        if addr == MAP_FAILED {
            perror(CString::new("Shared memory creation failed").unwrap().as_ptr());
            panic!("Failed to create shared memory");
        }
        println!("Created shared memory");
        ftruncate(fd, size_of::<SharedComms>() as i64);
        addr as *mut SharedComms
    }

    pub unsafe fn new() -> Self {
        let write_addr = SharedMemoryManager::create_shm(SHARED_MEMORY_PATH_WRAPPER);
        let read_addr = SharedMemoryManager::create_shm(SHARED_MEMORY_PATH_LOADER);

        libc::memset(write_addr as *mut libc::c_void, 0, size_of::<SharedComms>());

        ptr::write(write_addr, SharedComms::new(0));
        ptr::write(read_addr, SharedComms::new(0));

        SharedMemoryManager {
            shared_output: write_addr,
            shared_input: read_addr,
            last_read_conversation_id: 0,
            last_write_conversation_id: 0,
        }
    }

    pub unsafe fn read(&self) -> SharedComms {
        // if (*self.shared_input).key != WRAPPER_SHM_KEY {
        //     panic!("Shared memory read failed - no key!");
        // }
        while !(*self.shared_input).ready.load(Ordering::SeqCst) {
            thread::sleep(Duration::from_millis(200));
        }
        println!("Shared memory read");
        if (*self.shared_input).current_conversation_id == self.last_read_conversation_id {
            panic!("Shared memory read failed - no conversation!");
        }

        ptr::read(self.shared_input)
    }

    pub unsafe fn write(&mut self, request_id: CommID, data: &[u8]) {
        // lock
        (*self.shared_output).ready.store(false, Ordering::SeqCst);

        self.last_write_conversation_id += 1;
        (*self.shared_output).current_conversation_id = self.last_write_conversation_id;
        (*self.shared_output).request_id = request_id.as_u32();
        let size = data.len().min(MAX_SHARED_DATA_SIZE);
        (*self.shared_output).size = size;
        ptr::copy_nonoverlapping(
            data.as_ptr(),
            (*self.shared_output).data.as_mut_ptr(),
            size,
        );

        (*self.shared_output).ready.store(true, Ordering::SeqCst);
    }

    pub fn connect() {

    }

}