pub enum ResponseType {
    AirGap = 0,
    Kill = 1,
    Isolate = 2,
    Alert = 3,
    Run = 4
}

pub struct Response {
    pub type_: ResponseType,
    pub data: Option<String>,
}