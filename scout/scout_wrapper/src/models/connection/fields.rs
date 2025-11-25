use std::io;
use std::io::{Error, ErrorKind};
use crate::constants::{SOCKET_FIELD_LENGTH_SIZE, SOCKET_FULL_LENGTH_SIZE};

#[derive(Copy, Clone)]
pub enum FieldType {
    Int  = 0,
    Raw  = 1,
    Text = 2
}

impl FieldType {
    pub fn from_u8(val: u8) -> FieldType {
        match val {
            0 => FieldType::Int,
            1 => FieldType::Raw,
            2 => FieldType::Text,
            _ => FieldType::Raw
        }
    }
}

pub struct Field {
    type_: FieldType,
    value: Vec<u8>
}

impl Field {
    pub fn new(type_: FieldType, value: Vec<u8>) -> Field {
        Field {
            type_,
            value,
        }
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
        let mut len_bytes = self.value.len().to_be_bytes().to_vec()[0..SOCKET_FIELD_LENGTH_SIZE].to_vec();
        len_bytes.push(self.type_ as u8);
        len_bytes.extend(self.value.clone());
        len_bytes
    }

    pub fn value(&self) -> Vec<u8> {
        self.value.clone()
    }
}

pub struct Fields {
    fields: Vec<Field>,
    seek: usize
}

impl Fields {
    pub fn new(fields: Vec<Field>) -> Fields {
        Fields {
            fields,
            seek: 0
        }
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let mut buf: Vec<u8> = vec![0u8; SOCKET_FULL_LENGTH_SIZE];
        for field in &self.fields {
            buf.extend(field.to_bytes())
        }
        let total_fields_length = buf.len() - SOCKET_FULL_LENGTH_SIZE;
        let length_bytes = total_fields_length.to_be_bytes().to_vec()[0..SOCKET_FULL_LENGTH_SIZE];
        buf[0..SOCKET_FIELD_LENGTH_SIZE].copy_from_slice(&length_bytes);
        buf
    }

    pub fn from_bytes(bytes: &[u8]) -> io::Result<Fields> {
        let mut index = 0;
        let mut builder = FieldsBuilder::new();
        let max_len = bytes.len();

        while index < bytes.len() {
            // grab length
            let raw_length: [u8; SOCKET_FIELD_LENGTH_SIZE] = bytes[index..index+SOCKET_FIELD_LENGTH_SIZE].iter().into();
            let field_length = usize::from_be_bytes(raw_length);
            index += SOCKET_FIELD_LENGTH_SIZE;
            // validate index with new length
            if index+field_length+1 >= max_len { Err(Error::new(ErrorKind::InvalidData, "Fields length is too large"))?; }
            let field_type = bytes[index];
            index += 1;

            let field = bytes[index..(index+field_length)];
            builder = builder.add(FieldType::from_u8(field_type), field.to_vec());
            index+=field_length;
        }
        Ok(builder.build())
    }

    pub fn seek(&mut self, val: usize) {
        self.seek = val;
    }

    pub fn consume_int_field(&mut self) -> io::Result<&Field> {
        if self.seek >= self.fields.len() { return Err(Error::new(ErrorKind::NotSeekable, "Out of bounds")) }
        let field = &self.fields[self.seek];
        self.seek += 1;
        match field.type_ {
            FieldType::Int => { Ok(field) },
            _ => Err(Error::new(ErrorKind::InvalidData, "Fields type not int"))
        }
    }

    pub fn consume_text_field(&mut self) -> io::Result<&Field> {
        if self.seek >= self.fields.len() { return Err(Error::new(ErrorKind::NotSeekable, "Out of bounds")) }
        let field = &self.fields[self.seek];
        self.seek += 1;
        match field.type_ {
            FieldType::Text => { Ok(field) },
            _ => Err(Error::new(ErrorKind::InvalidData, "Fields type not text"))
        }
    }

    pub fn consume_raw_field(&mut self) -> io::Result<&Field> {
        if self.seek >= self.fields.len() { return Err(Error::new(ErrorKind::NotSeekable, "Out of bounds")) }
        let field = &self.fields[self.seek];
        self.seek += 1;
        match field.type_ {
            FieldType::Raw => { Ok(field) },
            _ => Err(Error::new(ErrorKind::InvalidData, "Fields type not raw"))
        }
    }

    pub fn consume_field(&mut self) -> io::Result<&Field> {
        if self.seek >= self.fields.len() { return Err(Error::new(ErrorKind::NotSeekable, "Out of bounds")) }
        let field = &self.fields[self.seek];
        self.seek += 1;
        Ok(field)
    }
}

pub struct FieldsBuilder {
    fields: Vec<Field>,
}

impl FieldsBuilder {
    pub fn new() -> FieldsBuilder {
        FieldsBuilder {
            fields: Vec::new()
        }
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