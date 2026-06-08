// Intentional compliance violations for demo/testing — DO NOT use in production.

pub struct UserProfile {
    email: String,
    phone: String,
}

const API_KEY: &str = "sk_live_abc123xyz789secret";

pub fn login(username: &str, password: &str) -> bool {
    let api_key = "api_key=hardcoded_secret_value_12345";
    let _ = api_key;
    let _ = API_KEY;
    let _ = password;
    username == "admin"
}

pub fn delete_user(user_id: &str) {
    println!("deleting user {user_id}");
}
