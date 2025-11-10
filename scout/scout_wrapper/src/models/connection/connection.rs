use std::io;
use std::io::{ErrorKind, Read, Write};
use std::net::{Shutdown, TcpStream};
use aes::Aes128;
use aes::cipher::block_padding::Pkcs7;
use aes::cipher::generic_array::GenericArray;
use bytemuck::{bytes_of, from_bytes, Pod};
use cbc::cipher::{BlockDecryptMut, BlockEncryptMut, KeyIvInit};
use cbc::{Decryptor, Encryptor};
use crate::constants::{SOCKET_FIELD_LENGTH_SIZE, SOCKET_FULL_LENGTH_SIZE};
use crate::models::connection::utils::{pkcs7_pad, pkcs7_unpad};

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

    pub fn send_raw(&mut self, buf: Vec<u8>) -> std::io::Result<()> {
        match &mut self.socket {
            None => {
                panic!("Connection not established yet");
            }
            Some(soc) => {
                soc.write_all(buf.as_slice())?;
            }
        }
        Ok(())
    }

    fn receive_raw(&mut self, len: usize) -> std::io::Result<Vec<u8>> {
        let mut buf = vec![0u8; len];
        match &mut self.socket {
            None => {
                panic!("Connection not established yet");
            },
            Some(soc) => {
                soc.read_exact(buf.as_mut_slice())?;
            }
        }
        Ok(buf)
    }

    fn get_cipher_enc(&self) -> Encryptor<Aes128> {
        if !self.in_encrypt_mode {
            panic!("Not in encryption mode yet!");
        }
        Encryptor::<Aes128>::new(&GenericArray::from(self.session_key), &GenericArray::from(self.iv))
    }

    fn get_cipher_dec(&self) -> Decryptor<Aes128> {
        if !self.in_encrypt_mode {
            panic!("Not in encryption mode yet!");
        }
        Decryptor::<Aes128>::new(&GenericArray::from(self.session_key), &GenericArray::from(self.iv))
    }

    fn encrypt_bytes(&mut self, buf: Vec<u8>) -> io::Result<Vec<u8>> {
        let mut cipher = self.get_cipher_enc();
        let mut out = buf.clone();
        cipher.encrypt_padded_vec_mut::<Pkcs7>(&mut out);
        Ok(out)
    }

    fn decrypt_bytes(&mut self, mut buf: Vec<u8>) -> io::Result<Vec<u8>> {
        let cipher = self.get_cipher_dec();
        match cipher.decrypt_padded_vec_mut::<Pkcs7>(&mut buf) {
            Ok(plaintext) => Ok(plaintext),
            Err(_) => Err(io::Error::new(ErrorKind::InvalidData, "bad padding or corrupt data")),
        }
    }

    pub fn encode_field<T: Pod>(&self, field: T) -> Vec<u8> {
        let bytes = bytes_of(&field);
        let len: [u8; 4] = (bytes.len() as u32).to_be_bytes();
        let mut out = Vec::with_capacity(4 + bytes.len());
        out.extend_from_slice(&len);
        out.extend_from_slice(bytes);
        out
    }

    fn decode_field<T: Pod>(&self, field: Vec<u8>) -> T {
        *from_bytes::<T>(&field)
    }

    pub fn set_in_encrypt_mode(&mut self, in_encrypt_mode: bool) {
        self.in_encrypt_mode = in_encrypt_mode;
    }

    pub fn receive_full(&mut self) -> Result<Vec<u8>, io::Error> {
        let full_len_raw = self.receive_raw(SOCKET_FULL_LENGTH_SIZE)?;
        if full_len_raw.len() != SOCKET_FULL_LENGTH_SIZE {
            return Err(io::Error::new(
                ErrorKind::InvalidData,
                "Expected full length of data",
            ))
        }
        let full_len = u32::from_be_bytes(full_len_raw.try_into().unwrap());

        let mut full_data_raw = self.receive_raw(full_len as usize)?;
        if self.in_encrypt_mode {
            full_data_raw = self.decrypt_bytes(full_data_raw)?;
        }

        Ok(full_data_raw)
    }

    pub fn read_field<T: Pod>(&mut self, buf: &mut &[u8]) -> Result<T, io::Error> {
        if buf.len() < SOCKET_FIELD_LENGTH_SIZE {
            return Err(io::Error::new(ErrorKind::UnexpectedEof, "missing length header"));
        }

        let (len_bytes, rest) = buf.split_at(SOCKET_FIELD_LENGTH_SIZE);
        let field_len = u32::from_be_bytes(len_bytes.try_into().unwrap()) as usize;

        if rest.len() < field_len {
            return Err(io::Error::new(ErrorKind::UnexpectedEof, "incomplete field data"));
        }

        let (field_raw, remaining) = rest.split_at(field_len);
        *buf = remaining;
        if field_raw.len() != size_of::<T>() {
            return Err(io::Error::new(ErrorKind::InvalidData, "size mismatch"));
        }

        Ok(*from_bytes::<T>(field_raw))
    }

    pub fn set_iv(&mut self, iv: [u8; 16]) {
        self.iv = iv.into();
    }

    pub fn set_session_key(&mut self, session_key: [u8; 32]) {
        self.session_key.copy_from_slice(&session_key[..16]);
    }
}
