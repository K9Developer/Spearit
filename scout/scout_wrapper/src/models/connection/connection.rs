use std::io;
use std::io::{ErrorKind, Read, Write};
use std::net::{Shutdown, TcpStream};
use aes::Aes128;
use aes::cipher::block_padding::{Pkcs7, UnpadError};
use aes::cipher::generic_array::GenericArray;
use cbc::cipher::{BlockDecryptMut, BlockEncryptMut, KeyIvInit};
use cbc::{Decryptor, Encryptor};
use crate::constants::{SOCKET_FIELD_LENGTH_SIZE, SOCKET_FULL_LENGTH_SIZE};
use crate::models::connection::fields::Fields;

pub struct Connection {
    iv: [u8; 16],
    session_key: [u8; 16],
    in_encrypt_mode: bool,

    socket: Option<TcpStream>,
}

impl Connection {
    pub fn new() -> Self {
        Connection {
            iv: [0; 16],
            session_key: [0; 16],
            in_encrypt_mode: false,
            socket: None,
        }
    }

    pub fn set_iv(&mut self, iv: [u8; 16]) { self.iv = iv.into(); }
    pub fn set_session_key(&mut self, session_key: [u8; 32]) { self.session_key.copy_from_slice(&session_key[..16]); }
    pub fn enable_encryption(&mut self) { self.in_encrypt_mode = true; }
    pub fn disable_encryption(&mut self) { self.in_encrypt_mode = false; }

    fn get_cipher_enc(&self) -> Encryptor<Aes128> {
        if !self.in_encrypt_mode { panic!("Not in encryption mode yet!"); }
        Encryptor::<Aes128>::new(&GenericArray::from(self.session_key), &GenericArray::from(self.iv))
    }
    fn get_cipher_dec(&self) -> Decryptor<Aes128> {
        if !self.in_encrypt_mode { panic!("Not in encryption mode yet!"); }
        Decryptor::<Aes128>::new(&GenericArray::from(self.session_key), &GenericArray::from(self.iv))
    }

    pub fn stop(&mut self) {
        if let Some(socket) = self.socket.take() {
            socket.shutdown(Shutdown::Both).unwrap()
        }
    }

    pub fn connect(&mut self, addr: &str) -> std::io::Result<()> {
        self.stop();
        self.socket = Some(TcpStream::connect(addr)?);
        Ok(())
    }

    fn recv_exact(&mut self, size: usize) -> io::Result<Vec<u8>> {
        let mut buf = vec![0u8; size];
        match &mut self.socket {
            None => panic!("Connection not established yet"),
            Some(soc) => soc.read_exact(buf.as_mut_slice())?
        }
        Ok(buf)
    }

    fn send_raw(&mut self, data: &[u8]) -> io::Result<()> {
        match &mut self.socket {
            None => panic!("Connection not established yet"),
            Some(soc) => soc.write_all(data)?
        }
        Ok(())
    }

    pub fn send_fields(&mut self, fields: Fields) -> io::Result<()> {
        let mut buf = fields.to_bytes();
        if self.in_encrypt_mode {
            let mut out;
            let enc = self.get_cipher_enc();
            enc.encrypt_padded_vec_mut::<Pkcs7>(&mut out);
            return self.send_raw(&out);
        }
        self.send_raw(buf.as_slice())
    }

    pub fn recv_fields(&mut self) -> io::Result<Fields> {
        let total_length_bytes = self.recv_exact(SOCKET_FULL_LENGTH_SIZE)?;
        let total_length = usize::from_be_bytes(total_length_bytes.into());
        let raw_fields = self.recv_exact(total_length)?;
        if self.in_encrypt_mode {
            let mut out;
            let dec = self.get_cipher_dec();
            match dec.decrypt_padded_vec_mut::<Pkcs7>(&mut out) {
                Err(_) => return Err(io::Error::new(ErrorKind::InvalidData, "bad padding or corrupt data")),
                _ => {}
            }
            return Fields::from_bytes(&out);
        }
        Fields::from_bytes(raw_fields.as_slice())
    }
}