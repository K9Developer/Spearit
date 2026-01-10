use crate::log_error;
use crate::models::connection::connection::Connection;
use crate::models::connection::fields::FieldsBuilder;
use crate::models::connection::message_trait::MessageTrait;
use rand_core::OsRng;
use sha2::{Digest, Sha256};
use std::io;
use std::io::Read;
use std::time::{SystemTime, UNIX_EPOCH};
use x25519_dalek::{EphemeralSecret, PublicKey};

pub struct HandshakeMessage {}

impl MessageTrait for HandshakeMessage {
    fn handle(mut conn: &mut Connection) -> io::Result<()> {
        // [Server -> Client] IV, PUB
        let mut server_iv_and_pub = conn.recv_fields()?;
        let server_iv: [u8; 16] = server_iv_and_pub
            .consume_raw_field()?
            .value()
            .as_slice()
            .try_into()
            .map_err(|_| {
                log_error!("Error converting server IV");
                io::Error::new(io::ErrorKind::InvalidData, "IV must be 16 bytes")
            })?;

        let server_pub_raw: [u8; 32] = server_iv_and_pub
            .consume_raw_field()?
            .value()
            .as_slice()
            .try_into()
            .map_err(|_| {
                log_error!("Error converting server public key");
                io::Error::new(io::ErrorKind::InvalidData, "Public key must be 32 bytes")
            })?;

        let server_pub = PublicKey::from(server_pub_raw);
        conn.set_iv(server_iv);

        // [Client -> Server] PUB
        let my_priv = EphemeralSecret::random_from_rng(OsRng);
        let my_pub = PublicKey::from(&my_priv);
        let my_pub_fields = FieldsBuilder::new(false)
            .add_raw(my_pub.as_bytes().to_vec())
            .build();
        conn.send_fields(my_pub_fields)?;

        // Calc sess key
        let shared = my_priv.diffie_hellman(&server_pub);
        let mut hasher = Sha256::new();
        hasher.update(shared.as_bytes());
        hasher.update(b"SpearIT-K9Dev");
        let session_key: [u8; 32] = hasher.finalize().into();
        conn.set_session_key(session_key);
        conn.enable_encryption();

        // [Server -> Client] timestamp
        let mut server_conf = conn.recv_fields()?;
        let server_ts: [u8; 8] = server_conf
            .consume_raw_field()?
            .value()
            .as_slice()
            .try_into()
            .map_err(|_| {
                log_error!("Error converting server timestamp");
                io::Error::new(io::ErrorKind::InvalidData, "Time stamp must be 8 bytes")
            })?;
        let restored_ts = u64::from_be_bytes(server_ts);
        let now_secs = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        let diff = now_secs as i64 - restored_ts as i64;
        if diff > 5 {
            log_error!("Server timestamp too far off! Diff: {} seconds", diff);
            return Err(io::Error::new(
                io::ErrorKind::Other,
                "Recieved invalid confirmation from server handshake!",
            ));
        }

        // [Client -> Server] timestamp
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs(); // u64
        let bytes = now.to_be_bytes();
        let fields = FieldsBuilder::new(false).add_raw(bytes.to_vec()).build();
        conn.send_fields(fields)?;

        Ok(())
    }
}
