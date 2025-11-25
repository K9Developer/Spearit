#[repr(C)]
#[derive(Clone, Copy)]
pub enum ResponseType {
    AirGap = 0,
    Kill = 1,
    Isolate = 2,
    Alert = 3,
    Run = 4
}

#[repr(C)]
#[derive(Copy, Clone)]
pub struct Response {
    pub type_: ResponseType,
}

#[repr(C)]
pub struct ResponseList {
    pub responses: [Response; 5],
    pub length: usize,
}