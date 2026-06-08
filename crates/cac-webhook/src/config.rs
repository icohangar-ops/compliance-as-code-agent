use std::path::PathBuf;

#[derive(Debug, Clone)]
pub struct WebhookConfig {
    pub bind_addr: String,
    pub webhook_secret: String,
    pub policies_dir: PathBuf,
    pub work_dir: PathBuf,
    pub signing_key: Option<String>,
    pub github_token: Option<String>,
    pub codeberg_token: Option<String>,
    pub auto_fix_pr: bool,
    pub status_context: String,
    pub public_url: Option<String>,
}

impl WebhookConfig {
    pub fn from_env(policies_dir: PathBuf) -> Self {
        Self {
            bind_addr: std::env::var("CAC_BIND_ADDR").unwrap_or_else(|_| "0.0.0.0:8080".into()),
            webhook_secret: std::env::var("CAC_WEBHOOK_SECRET")
                .unwrap_or_else(|_| "change-me".into()),
            policies_dir,
            work_dir: std::env::var("CAC_WORK_DIR")
                .map(PathBuf::from)
                .unwrap_or_else(|_| std::env::temp_dir().join("cac-webhook")),
            signing_key: std::env::var("CAC_LEDGER_SIGNING_KEY").ok(),
            github_token: std::env::var("CAC_GITHUB_TOKEN").ok(),
            codeberg_token: std::env::var("CAC_CODEBERG_TOKEN").ok(),
            auto_fix_pr: std::env::var("CAC_AUTO_FIX_PR")
                .map(|v| v == "1" || v.eq_ignore_ascii_case("true"))
                .unwrap_or(false),
            status_context: std::env::var("CAC_STATUS_CONTEXT")
                .unwrap_or_else(|_| "compliance-as-code/scan".into()),
            public_url: std::env::var("CAC_PUBLIC_URL").ok(),
        }
    }
}
