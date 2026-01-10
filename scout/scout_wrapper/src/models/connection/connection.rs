use crate::constants::{ENABLE_ENCRYPTION, SOCKET_FIELD_LENGTH_SIZE, SOCKET_FULL_LENGTH_SIZE};
use crate::models::connection::fields::{Fields, FieldsBuilder};
use crate::{log_error, log_warn};
use aes::Aes128;
use aes::cipher::block_padding::{Pkcs7, UnpadError};
use aes::cipher::generic_array::GenericArray;
use cbc::cipher::{BlockDecryptMut, BlockEncryptMut, KeyIvInit};
use cbc::{Decryptor, Encryptor};
use std::io::{self, Error};
use std::io::{ErrorKind, Read, Write};
use std::net::{Shutdown, TcpStream};

pub struct Connection {
    iv: [u8; 16],
    session_key: [u8; 16],
    in_encrypt_mode: bool,

    socket: Option<TcpStream>,

    pending_data: Vec<u8>,
}

impl Connection {
    pub fn new() -> Self {
        Connection {
            iv: [0; 16],
            session_key: [0; 16],
            in_encrypt_mode: false,
            socket: None,

            pending_data: vec![],
        }
    }

    pub fn set_iv(&mut self, iv: [u8; 16]) {
        self.iv = iv.into();
    }
    pub fn set_session_key(&mut self, session_key: [u8; 32]) {
        self.session_key.copy_from_slice(&session_key[..16]);
    }
    pub fn enable_encryption(&mut self) {
        if !ENABLE_ENCRYPTION {
            log_warn!("Encryption is disabled via constants. Not enabling encryption.");
            return;
        }
        self.in_encrypt_mode = true;
    }
    pub fn disable_encryption(&mut self) {
        self.in_encrypt_mode = false;
    }

    fn get_cipher_enc(&self) -> Encryptor<Aes128> {
        if !self.in_encrypt_mode {
            panic!("Not in encryption mode yet!");
        }
        Encryptor::<Aes128>::new(
            &GenericArray::from(self.session_key),
            &GenericArray::from(self.iv),
        )
    }
    fn get_cipher_dec(&self) -> Decryptor<Aes128> {
        if !self.in_encrypt_mode {
            panic!("Not in encryption mode yet!");
        }
        Decryptor::<Aes128>::new(
            &GenericArray::from(self.session_key),
            &GenericArray::from(self.iv),
        )
    }

    pub fn stop(&mut self) {
        if let Some(socket) = self.socket.take() {
            socket.shutdown(Shutdown::Both);
        }
    }

    pub fn connect(&mut self, addr: &str) -> std::io::Result<()> {
        self.stop();
        self.socket = Some(TcpStream::connect(addr)?);
        Ok(())
    }

    pub fn reset(&mut self) {
        self.stop();
        self.in_encrypt_mode = false;
        self.session_key = [0; 16];
        self.iv = [0; 16];
    }

    fn recv_exact(&mut self, size: usize) -> io::Result<Vec<u8>> {
        let mut buf = vec![0u8; size];

        let mut bytes_to_read = size;
        if self.pending_data.len() > 0 {
            let to_copy = bytes_to_read.min(self.pending_data.len());
            buf[..to_copy].copy_from_slice(&self.pending_data[..to_copy]);
            self.pending_data.drain(..to_copy);
            bytes_to_read -= to_copy;
        }

        match &mut self.socket {
            None => panic!("Connection not established yet"),
            Some(soc) => soc.read_exact(&mut buf[size - bytes_to_read..])?,
        }
        Ok(buf)
    }

    fn recv_exact_non_blocking(&mut self, size: usize) -> Result<Vec<u8>, ()> {
        let res = match &mut self.socket {
            None => Err(()),
            Some(soc) => {
                soc.set_read_timeout(Some(std::time::Duration::from_millis(5)))
                    .map_err(|_| ())?;
                while self.pending_data.len() < size {
                    let mut tmp = [0u8; 4096];

                    match soc.read(&mut tmp) {
                        Ok(0) => {
                            return Err(());
                        }
                        Ok(n) => {
                            self.pending_data.extend_from_slice(&tmp[..n]);
                        }
                        Err(e)
                            if e.kind() == ErrorKind::WouldBlock
                                || e.kind() == ErrorKind::TimedOut =>
                        {
                            log_warn!("Socket would block or timed out");
                            return Err(());
                        }
                        Err(e) => return Err(()),
                    }
                }

                let out = self.pending_data[..size].to_vec();
                self.pending_data.drain(..size);
                Ok(out)
            }
        };

        match &self.socket {
            None => {}
            Some(soc) => {
                soc.set_read_timeout(None).map_err(|_| ())?;
            }
        }

        res
    }

    fn send_raw(&mut self, data: &[u8]) -> io::Result<()> {
        match &mut self.socket {
            None => panic!("Connection not established yet"),
            Some(soc) => soc.write_all(data)?,
        }
        Ok(())
    }

    pub fn send_fields(&mut self, fields: Fields) -> io::Result<()> {
        if self.in_encrypt_mode {
            let enc = self.get_cipher_enc();
            let out = enc.encrypt_padded_vec_mut::<Pkcs7>(fields.to_bytes_no_length().as_slice());
            let encrypted_fields = FieldsBuilder::new(false).add_raw(out).build();

            return self.send_raw(encrypted_fields.to_bytes().as_slice());
        }
        let mut buf = fields.to_bytes();
        return self.send_raw(buf.as_slice());
    }

    pub fn recv_fields(&mut self) -> io::Result<Fields> {
        let total_length_bytes = self.recv_exact(SOCKET_FULL_LENGTH_SIZE)?;
        let total_length = usize::from_be_bytes(
            total_length_bytes
                .as_slice()
                .try_into()
                .expect("Expected exactly 8 bytes for total_length"),
        );
        let raw_fields = self.recv_exact(total_length)?;
        if self.in_encrypt_mode {
            let dec = self.get_cipher_dec();
            let mut out = dec.decrypt_padded_vec_mut::<Pkcs7>(raw_fields.as_slice());
            match out {
                Err(_) => {
                    return Err(io::Error::new(
                        ErrorKind::InvalidData,
                        "bad padding or corrupt data",
                    ));
                }
                Ok(o) => return Fields::from_bytes(o.as_slice()),
            }
        }
        Fields::from_bytes(raw_fields.as_slice())
    }

    pub fn recv_fields_non_blocking(&mut self) -> Result<Fields, ()> {
        let total_length_bytes = self
            .recv_exact_non_blocking(SOCKET_FULL_LENGTH_SIZE)
            .map_err(|_| ())?;
        let total_length =
            usize::from_be_bytes(total_length_bytes.as_slice().try_into().map_err(|_| ())?);
        let raw_fields = self.recv_exact_non_blocking(total_length)?;
        if self.in_encrypt_mode {
            let dec = self.get_cipher_dec();
            let mut out = dec.decrypt_padded_vec_mut::<Pkcs7>(raw_fields.as_slice());
            match out {
                Err(_) => {
                    return Err(());
                }
                Ok(o) => return Fields::from_bytes(o.as_slice()).map_err(|_| ()),
            }
        }
        Fields::from_bytes(raw_fields.as_slice()).map_err(|_| ())
    }

    pub fn is_connected(&mut self) -> bool {
        match &mut self.socket {
            None => false,
            Some(soc) => soc.peer_addr().is_ok(),
        }
    }
}
