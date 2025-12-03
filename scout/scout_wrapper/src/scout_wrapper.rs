use crate::models::connection::connection::Connection;

// TODO: [8 bytes to signify full message length]
// [4 bytes to signify the goal of the message]
// [4 bytes to signify field 1 length]
// [x bytes for field 1]
// [4 bytes to signify field 2 length]
// [x bytes for field 2]
// TODO: In rule have order and ID, also have type (FROM_AIRGAP, USER, SYSTEM)

enum ScoutWrapperState {
    NotConnected,
    Connected
}

pub struct ScoutWrapper {
    conn: Connection,
    state: ScoutWrapperState
//     write_shared_mem
//     read_shared_mem

}

impl ScoutWrapper {
    // pub fn new() -> ScoutWrapper {}
    //
    // pub fn start() // will loop
    //
    // fn read_new_event()
    // fn write_new_rule()
    //
    // fn on_new_rule()
    //
    // fn send_heartbeat()
    // fn send_violation()

}