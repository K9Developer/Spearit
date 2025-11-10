use std::io::Read;
use std::time::{SystemTime, UNIX_EPOCH};
use rand_core::OsRng;
use x25519_dalek::{EphemeralSecret, PublicKey};
use crate::models::connection::connection::Connection;
use crate::models::connection::message_trait::MessageTrait;
use sha2::{Sha256, Digest};

pub struct Handshake {}

impl MessageTrait for Handshake {
    fn handle(mut conn: Connection) -> Result<(), std::io::Error> {
        // [Server -> Client] IV, PUB
        let mut server_iv_and_pub = conn.receive_full()?;
        let server_iv: [u8; 16] = conn.read_field(&mut server_iv_and_pub.as_slice())?;
        let server_pub_raw: [u8; 32] = conn.read_field(&mut server_iv_and_pub.as_slice())?;
        let server_pub = PublicKey::from(server_pub_raw);
        conn.set_iv(server_iv);

        // [Client -> Server] PUB
        let my_priv = EphemeralSecret::random_from_rng(OsRng);
        let my_pub = PublicKey::from(&my_priv);
        conn.send_raw(conn.encode_field(*my_pub.as_bytes()))?;

        // Calc sess key
        let shared = my_priv.diffie_hellman(&server_pub);
        let mut hasher = Sha256::new();
        hasher.update(shared.as_bytes());
        hasher.update(b"SpearIT-K9Dev");
        let session_key: [u8; 32]  = hasher.finalize().into();

        conn.set_session_key(session_key);
        conn.set_in_encrypt_mode(true);

        // [Server -> Client] timestamp
        let mut server_conf = conn.receive_full()?;
        let server_ts: [u8; 8] = conn.read_field(&mut server_conf.as_slice())?;
        let restored_ts = u64::from_be_bytes(server_ts);
        let now_secs = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();
        let diff = now_secs as i64 - restored_ts as i64;

        if diff > 2 {
            return Err(std::io::Error::new(
                std::io::ErrorKind::Other,
                "Recieved invalid confirmation from server handshake!"
            ))
        }

        // [Client -> Server] timestamp
        let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();           // u64
        let bytes = now.to_be_bytes();
        conn.send_raw(conn.encode_field(bytes))?;

        Ok(())
    }
}