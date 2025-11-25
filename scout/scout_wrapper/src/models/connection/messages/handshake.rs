use std::io;
use std::io::Read;
use std::time::{SystemTime, UNIX_EPOCH};
use rand_core::OsRng;
use x25519_dalek::{EphemeralSecret, PublicKey};
use crate::models::connection::connection::Connection;
use crate::models::connection::message_trait::MessageTrait;
use sha2::{Sha256, Digest};
use crate::models::connection::fields::FieldsBuilder;

pub struct Handshake {}

impl MessageTrait for Handshake {
    fn handle(mut conn: Connection) -> io::Result<()> {
        // [Server -> Client] IV, PUB
        let mut server_iv_and_pub = conn.recv_fields()?;
        let server_iv: [u8; 16] = server_iv_and_pub.consume_raw_field()?.value().into();
        let server_pub_raw: [u8; 32] = server_iv_and_pub.consume_raw_field()?.value().into();
        let server_pub = PublicKey::from(server_pub_raw);
        conn.set_iv(server_iv);

        // // [Client -> Server] PUB
        let my_priv = EphemeralSecret::random_from_rng(OsRng);
        let my_pub = PublicKey::from(&my_priv);
        let my_pub_fields = FieldsBuilder::new().add_raw(my_pub.as_bytes().to_vec()).build();
        conn.send_fields(my_pub_fields)?;

        // Calc sess key
        let shared = my_priv.diffie_hellman(&server_pub);
        let mut hasher = Sha256::new();
        hasher.update(shared.as_bytes());
        hasher.update(b"SpearIT-K9Dev");
        let session_key: [u8; 32]  = hasher.finalize().into();
        conn.set_session_key(session_key);
        conn.enable_encryption();

        let mut server_conf = conn.recv_fields()?;
        let server_ts: [u8; 8] = server_conf.consume_raw_field()?.value().into();
        let restored_ts = u64::from_be_bytes(server_ts);
        let now_secs = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();
        let diff = now_secs as i64 - restored_ts as i64;
        if diff > 2 {
            return Err(io::Error::new(
                io::ErrorKind::Other,
                "Recieved invalid confirmation from server handshake!"
            ))
        }

        // [Client -> Server] timestamp
        let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();           // u64
        let bytes = now.to_be_bytes();
        let fields = FieldsBuilder::new().add_raw(bytes.to_vec()).build();
        conn.send_fields(fields)?;

        Ok(())
    }
}