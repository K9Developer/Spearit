use crate::constants::{
    LOADER_SHM_KEY, MAX_SHARED_DATA_SIZE, SHARED_MEMORY_PATH_LOADER, SHARED_MEMORY_PATH_WRAPPER,
    WRAPPER_SHM_KEY,
};
use crate::models::rules::rule::CompiledRule;
use crate::{log_debug, log_error, log_warn};
use libc::{
    MAP_FAILED, MAP_SHARED, O_CREAT, O_RDWR, PROT_READ, PROT_WRITE, PTHREAD_MUTEX_ROBUST,
    PTHREAD_PROCESS_SHARED, c_char, c_int, ftruncate, mmap, perror, pthread_mutex_init,
    pthread_mutex_lock, pthread_mutex_t, pthread_mutex_trylock, pthread_mutex_unlock,
    pthread_mutexattr_destroy, pthread_mutexattr_init, pthread_mutexattr_setpshared,
    pthread_mutexattr_setrobust, pthread_mutexattr_t, size_t, strerror,
};
use std::ffi::{CStr, CString};
use std::mem::offset_of;
use std::ptr::null;
use std::sync::atomic::{AtomicBool, Ordering};
use std::time::Duration;
use std::{mem, ptr, thread};

unsafe extern "C" {
    pub fn shm_open(name: *const c_char, oflag: c_int, mode: c_int) -> c_int;
    pub fn shm_unlink(name: *const c_char) -> c_int;
}

#[repr(C)]
#[derive(Debug, Clone, Copy)]
pub enum CommID {
    None = 0,
    ReqActiveRuleIds = 1,
    ReqRuleData = 2,
    ResRuleViolation = 3,
    ResActiveRuleIds = 4,
    ResRuleData = 5,
    ResNetworkInfoUpdate = 6,
}

impl CommID {
    pub fn from_u32(value: u32) -> Option<Self> {
        match value {
            0 => Some(CommID::None),
            1 => Some(CommID::ReqActiveRuleIds),
            2 => Some(CommID::ReqRuleData),
            3 => Some(CommID::ResRuleViolation),
            4 => Some(CommID::ResActiveRuleIds),
            5 => Some(CommID::ResRuleData),
            6 => Some(CommID::ResNetworkInfoUpdate),
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
    pub current_conversation_id: i32,
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
    pub lock: pthread_mutex_t,
    pub current_conversation_id: u32,
    pub request_id: u32,
    pub size: usize,
    pub data: [u8; MAX_SHARED_DATA_SIZE],
}

impl SharedComms {
    pub fn new(key: usize) -> Self {
        SharedComms {
            key,
            size: 0,
            lock: unsafe { mem::zeroed() },
            current_conversation_id: 0,
            request_id: 0,
            data: [0u8; MAX_SHARED_DATA_SIZE],
        }
    }
}

pub struct SharedMemoryManager {
    shared_input: *mut SharedComms,
    shared_output: *mut SharedComms,

    mutex_attr_input: pthread_mutexattr_t,
    mutex_attr_output: pthread_mutexattr_t,

    last_conversation_id: u32,
}

impl SharedMemoryManager {
    unsafe fn create_shm(name: &str) -> *mut SharedComms {
        unsafe {
            let name = CString::new(name).unwrap();
            let fd: c_int = shm_open(name.as_ptr(), O_CREAT | O_RDWR, 0600);
            if fd < 0 {
                log_error!(
                    "Shared memory opening failed: {}",
                    CStr::from_ptr(strerror(*libc::__errno_location())).to_string_lossy()
                );
                panic!("Failed to open shared memory");
            }
            log_debug!("Opened shared memory: {}", name.to_string_lossy());
            let size = size_of::<SharedComms>();

            if ftruncate(fd, size as i64) < 0 {
                log_error!(
                    "Failed to truncate shared memory: {}",
                    CStr::from_ptr(strerror(*libc::__errno_location())).to_string_lossy()
                );
                panic!("Failed to truncate shared memory");
            }

            let addr = mmap(
                ptr::null_mut(),
                size as size_t,
                PROT_READ | PROT_WRITE,
                MAP_SHARED,
                fd,
                0,
            );

            if addr == MAP_FAILED {
                log_error!(
                    "Shared memory creation failed: {}",
                    CStr::from_ptr(strerror(*libc::__errno_location())).to_string_lossy()
                );
                panic!("Failed to create shared memory");
            }
            log_debug!("Created shared memory at address: {:p}", addr);
            addr as *mut SharedComms
        }
    }

    fn init_shared_mutex(mutex: *mut pthread_mutex_t, attr: *mut pthread_mutexattr_t) {
        unsafe {
            pthread_mutexattr_init(attr);
            pthread_mutexattr_setpshared(attr, PTHREAD_PROCESS_SHARED);
            pthread_mutexattr_setrobust(attr, PTHREAD_MUTEX_ROBUST);

            let ret = libc::pthread_mutex_init(mutex, attr);
            if ret != 0 {
                log_error!(
                    "Failed to initialize shared mutex: {}",
                    CStr::from_ptr(strerror(ret)).to_string_lossy()
                );
                panic!("Failed to initialize shared mutex");
            }
            pthread_mutexattr_destroy(attr);
        }
    }

    pub unsafe fn new() -> Self {
        unsafe {
            let write_addr = SharedMemoryManager::create_shm(SHARED_MEMORY_PATH_WRAPPER);
            let read_addr = SharedMemoryManager::create_shm(SHARED_MEMORY_PATH_LOADER);

            libc::memset(write_addr as *mut libc::c_void, 0, size_of::<SharedComms>());

            ptr::write(write_addr, SharedComms::new(1));
            ptr::write(read_addr, SharedComms::new(1));

            let mut mutex_attr_output: pthread_mutexattr_t = mem::zeroed();
            let mut mutex_attr_input: pthread_mutexattr_t = mem::zeroed();

            SharedMemoryManager::init_shared_mutex(&mut (*write_addr).lock, &mut mutex_attr_output);
            SharedMemoryManager::init_shared_mutex(&mut (*read_addr).lock, &mut mutex_attr_input);

            SharedMemoryManager {
                shared_output: write_addr,
                shared_input: read_addr,
                last_conversation_id: 0,

                mutex_attr_input,
                mutex_attr_output,
            }
        }
    }

    pub unsafe fn read(&mut self, expected_conversation_id: i32) -> Option<SharedComms> {
        unsafe {
            pthread_mutex_lock(&mut (*self.shared_input).lock);
            let valid_id = if expected_conversation_id >= 0 {
                ((*self.shared_input).current_conversation_id as i32) == expected_conversation_id
            } else {
                (*self.shared_input).current_conversation_id != self.last_conversation_id
            };
            if !valid_id {
                pthread_mutex_unlock(&mut (*self.shared_input).lock);
                return None;
            }

            let d = ptr::read(self.shared_input);
            pthread_mutex_unlock(&mut (*self.shared_input).lock);
            self.last_conversation_id = d.current_conversation_id;
            Some(d)
        }
    }

    pub unsafe fn write(&mut self, request_id: CommID, data: &[u8], conversation_id: i32) {
        unsafe {
            pthread_mutex_lock(&mut (*self.shared_output).lock);
            (*self.shared_output).current_conversation_id = if (conversation_id >= 0) {
                conversation_id as u32
            } else {
                self.last_conversation_id + 1
            };
            (*self.shared_output).request_id = request_id.as_u32();
            let size = data.len().min(MAX_SHARED_DATA_SIZE);

            (*self.shared_output).size = size;
            ptr::copy_nonoverlapping(data.as_ptr(), (*self.shared_output).data.as_mut_ptr(), size);
            pthread_mutex_unlock(&mut (*self.shared_output).lock);
            self.last_conversation_id = (*self.shared_output).current_conversation_id;
        }
    }

    pub unsafe fn connect(&mut self) {
        unsafe {
            log_debug!("Connecting to shared memory...");
            (*self.shared_output).key = WRAPPER_SHM_KEY;
            while (*self.shared_input).key != LOADER_SHM_KEY {
                thread::sleep(Duration::from_millis(200));
            }
            log_debug!("Connected to shared memory");
        }
    }
}
