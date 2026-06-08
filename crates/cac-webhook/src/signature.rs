use hmac::{Hmac, Mac};
use sha2::Sha256;
use subtle::ConstantTimeEq;

type HmacSha256 = Hmac<Sha256>;

pub fn verify_github_signature(secret: &str, body: &[u8], header: &str) -> bool {
    let Some(digest) = header.strip_prefix("sha256=") else {
        return false;
    };
    let Ok(expected) = hex::decode(digest) else {
        return false;
    };
    let Ok(actual) = compute_hmac(secret, body) else {
        return false;
    };
    expected.ct_eq(&actual).into()
}

pub fn verify_gitea_signature(secret: &str, body: &[u8], header: &str) -> bool {
    let Ok(expected) = hex::decode(header) else {
        return false;
    };
    let Ok(actual) = compute_hmac(secret, body) else {
        return false;
    };
    expected.ct_eq(&actual).into()
}

pub fn github_signature(secret: &str, body: &[u8]) -> String {
    let mac = compute_hmac(secret, body).expect("hmac");
    format!("sha256={}", hex::encode(mac))
}

pub fn gitea_signature(secret: &str, body: &[u8]) -> String {
    let mac = compute_hmac(secret, body).expect("hmac");
    hex::encode(mac)
}

fn compute_hmac(secret: &str, body: &[u8]) -> Result<Vec<u8>, hmac::digest::InvalidLength> {
    let mut mac = HmacSha256::new_from_slice(secret.as_bytes())?;
    mac.update(body);
    Ok(mac.finalize().into_bytes().to_vec())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn github_signature_roundtrip() {
        let body = br#"{"action":"opened"}"#;
        let sig = github_signature("test-secret", body);
        assert!(verify_github_signature("test-secret", body, &sig));
        assert!(!verify_github_signature("wrong", body, &sig));
    }

    #[test]
    fn gitea_signature_roundtrip() {
        let body = br#"{"action":"opened"}"#;
        let sig = gitea_signature("test-secret", body);
        assert!(verify_gitea_signature("test-secret", body, &sig));
    }
}
