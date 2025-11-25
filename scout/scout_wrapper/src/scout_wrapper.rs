use crate::models::connection::connection::Connection;

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