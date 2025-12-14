use crate::models::connection::connection::Connection;

pub trait MessageTrait {
    fn handle(conn: &mut Connection) -> Result<(), std::io::Error>;
}
