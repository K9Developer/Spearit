use crate::constants::{GLOBAL_STATE, SOCKET_FIELD_LENGTH_SIZE, SOCKET_FULL_LENGTH_SIZE};
use crate::log_error;
use std::fmt::Debug;
use std::io;
use std::io::{Error, ErrorKind};

#[derive(Copy, Clone, Debug)]
pub enum FieldType {
    Int = 0,
    Raw = 1,
    Text = 2,
}

impl FieldType {
    pub fn from_u8(val: u8) -> FieldType {
        match val {
            0 => FieldType::Int,
            1 => FieldType::Raw,
            2 => FieldType::Text,
            _ => FieldType::Raw,
        }
    }
}

pub struct Field {
    type_: FieldType,
    value: Vec<u8>,
}

impl Field {
    pub fn new(type_: FieldType, value: Vec<u8>) -> Field {
        Field { type_, value }
    }

    pub fn new_int(value: i64) -> Field {
        Field {
            type_: FieldType::Int,
            value: value.to_be_bytes().to_vec(),
        }
    }

    pub fn new_raw(value: Vec<u8>) -> Field {
        Field {
            type_: FieldType::Raw,
            value,
        }
    }

    pub fn new_str(value: String) -> Field {
        Field {
            type_: FieldType::Text,
            value: value.into_bytes(),
        }
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let mut len_bytes = (self.value.len() as u32 + 1).to_be_bytes().to_vec()
            [0..SOCKET_FIELD_LENGTH_SIZE]
            .to_vec();
        len_bytes.push(self.type_ as u8);
        len_bytes.extend(self.value.clone());
        len_bytes
    }

    pub fn value(&self) -> Vec<u8> {
        self.value.clone()
    }

    pub fn as_str(&self) -> String {
        match String::from_utf8(self.value.clone()) {
            Ok(s) => s,
            Err(e) => String::new(),
        }
    }

    pub fn as_int(&self) -> i64 {
        if self.value.len() != 8 {
            log_error!("Field value length is not 8 bytes for int conversion");
            return 0;
        }
        let arr: [u8; 8] = self.value.clone().try_into().unwrap_or([0; 8]);
        i64::from_be_bytes(arr)
    }
}

impl Debug for Field {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Field")
            .field("type_", &self.type_)
            .field("value", &self.value)
            .finish()
    }
}

pub struct Fields {
    fields: Vec<Field>,
    seek: usize,
}

impl Fields {
    pub fn new(fields: Vec<Field>) -> Fields {
        Fields { fields, seek: 0 }
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let mut buf: Vec<u8> = vec![0u8; SOCKET_FULL_LENGTH_SIZE];
        for field in &self.fields {
            buf.extend(field.to_bytes());
        }
        let total_fields_length = buf.len() - SOCKET_FULL_LENGTH_SIZE;
        let length_bytes = &total_fields_length.to_be_bytes().to_vec()[0..SOCKET_FULL_LENGTH_SIZE];
        buf[0..SOCKET_FULL_LENGTH_SIZE].copy_from_slice(length_bytes);
        buf
    }

    pub fn to_bytes_no_length(&self) -> Vec<u8> {
        let mut buf: Vec<u8> = Vec::new();
        for field in &self.fields {
            buf.extend(field.to_bytes())
        }
        buf
    }

    pub fn from_bytes(bytes: &[u8]) -> io::Result<Fields> {
        let mut index = 0;
        let mut builder = FieldsBuilder::new(false);
        let max_len = bytes.len();

        while index < bytes.len() {
            // grab length
            let raw_length: [u8; SOCKET_FIELD_LENGTH_SIZE] = bytes
                [index..index + SOCKET_FIELD_LENGTH_SIZE]
                .try_into()
                .expect("slice has wrong length");
            let field_length = u32::from_be_bytes(raw_length) as usize;

            index += SOCKET_FIELD_LENGTH_SIZE;
            if index + field_length > max_len {
                Err(Error::new(
                    ErrorKind::InvalidData,
                    "Fields length is too large",
                ))?;
            }
            let field_type = bytes[index];

            let field = &bytes[index + 1..(index + field_length)];
            builder = builder.add(FieldType::from_u8(field_type), field.to_vec());
            index += field_length;
        }
        Ok(builder.build())
    }

    pub fn seek(&mut self, val: usize) {
        self.seek = val;
    }

    pub fn consume_int_field(&mut self) -> io::Result<&Field> {
        if self.seek >= self.fields.len() {
            return Err(Error::new(ErrorKind::NotSeekable, "Out of bounds"));
        }
        let field = &self.fields[self.seek];
        self.seek += 1;
        match field.type_ {
            FieldType::Int => Ok(field),
            _ => Err(Error::new(ErrorKind::InvalidData, "Fields type not int")),
        }
    }

    pub fn consume_text_field(&mut self) -> io::Result<&Field> {
        if self.seek >= self.fields.len() {
            return Err(Error::new(ErrorKind::NotSeekable, "Out of bounds"));
        }
        let field = &self.fields[self.seek];
        self.seek += 1;
        match field.type_ {
            FieldType::Text => Ok(field),
            _ => Err(Error::new(ErrorKind::InvalidData, "Fields type not text")),
        }
    }

    pub fn consume_raw_field(&mut self) -> io::Result<&Field> {
        if self.seek >= self.fields.len() {
            return Err(Error::new(ErrorKind::NotSeekable, "Out of bounds"));
        }
        let field = &self.fields[self.seek];
        self.seek += 1;
        match field.type_ {
            FieldType::Raw => Ok(field),
            _ => Err(Error::new(ErrorKind::InvalidData, "Fields type not raw")),
        }
    }

    pub fn consume_field(&mut self) -> io::Result<&Field> {
        if self.seek >= self.fields.len() {
            return Err(Error::new(ErrorKind::NotSeekable, "Out of bounds"));
        }
        let field = &self.fields[self.seek];
        self.seek += 1;
        Ok(field)
    }
}

impl Debug for Fields {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Fields")
            .field("fields", &self.fields)
            .field("seek", &self.seek)
            .finish()
    }
}

pub struct FieldsBuilder {
    fields: Vec<Field>,
}

impl FieldsBuilder {
    pub fn new(add_mac: bool) -> FieldsBuilder {
        let mut fields: Vec<Field> = Vec::new();
        if add_mac {
            // TODO: Optimize by passing mac as param (?)
            fields.push(Field::new_str(
                GLOBAL_STATE
                    .lock()
                    .unwrap()
                    .mac_address
                    .clone()
                    .unwrap_or("00:00:00:00:00:00".to_string()),
            ));
        }
        FieldsBuilder { fields }
    }

    pub fn add_int(mut self, value: i64) -> Self {
        self.fields.push(Field::new_int(value));
        self
    }

    pub fn add_raw(mut self, value: Vec<u8>) -> Self {
        self.fields.push(Field::new_raw(value));
        self
    }

    pub fn add_str(mut self, value: String) -> Self {
        self.fields.push(Field::new_str(value));
        self
    }

    pub fn add(mut self, type_: FieldType, value: Vec<u8>) -> Self {
        self.fields.push(Field::new(type_, value));
        self
    }

    pub fn build(self) -> Fields {
        Fields::new(self.fields)
    }
}
