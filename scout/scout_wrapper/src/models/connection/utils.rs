pub fn pkcs7_pad(data: &[u8]) -> Vec<u8> {
    let pad_len = 16 - (data.len() % 16);
    let mut out = data.to_vec();
    out.extend(std::iter::repeat(pad_len as u8).take(pad_len));
    out
}

pub fn pkcs7_unpad(data: &[u8]) -> std::io::Result<Vec<u8>> {
    if data.is_empty() {
        return Err(std::io::Error::new(std::io::ErrorKind::InvalidData, "empty"));
    }
    let pad_len = *data.last().unwrap() as usize;
    if pad_len == 0 || pad_len > 16 || data.len() < pad_len {
        return Err(std::io::Error::new(std::io::ErrorKind::InvalidData, "bad padding"));
    }
    Ok(data[..data.len() - pad_len].to_vec())
}
