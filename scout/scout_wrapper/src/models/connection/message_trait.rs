use crate::models::connection::connection::Connection;

pub trait MessageTrait {
    fn handle(conn: Connection) -> Result<(), std::io::Error>;
}