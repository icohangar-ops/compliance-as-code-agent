use crate::payload::ProviderKind;
use reqwest::Client;
use serde::Serialize;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum ProviderError {
    #[error("http error: {0}")]
    Http(#[from] reqwest::Error),
    #[error("api error ({status}): {body}")]
    Api { status: u16, body: String },
    #[error("missing token for {0}")]
    MissingToken(&'static str),
}

#[derive(Debug, Clone, Serialize)]
struct CommitStatus<'a> {
    state: &'a str,
    context: &'a str,
    description: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    target_url: Option<String>,
}

pub struct ProviderClient {
    http: Client,
    github_token: Option<String>,
    codeberg_token: Option<String>,
}

impl ProviderClient {
    pub fn new(github_token: Option<String>, codeberg_token: Option<String>) -> Self {
        Self {
            http: Client::new(),
            github_token,
            codeberg_token,
        }
    }

    pub async fn set_pending(
        &self,
        provider: ProviderKind,
        owner: &str,
        repo: &str,
        sha: &str,
        context: &str,
    ) -> Result<(), ProviderError> {
        self.set_status(
            provider,
            owner,
            repo,
            sha,
            context,
            "pending",
            "Compliance scan in progress".into(),
            None,
        )
        .await
    }

    pub async fn set_result(
        &self,
        provider: ProviderKind,
        owner: &str,
        repo: &str,
        sha: &str,
        context: &str,
        passed: bool,
        description: String,
        target_url: Option<String>,
    ) -> Result<(), ProviderError> {
        self.set_status(
            provider,
            owner,
            repo,
            sha,
            context,
            if passed { "success" } else { "failure" },
            description,
            target_url,
        )
        .await
    }

    async fn set_status(
        &self,
        provider: ProviderKind,
        owner: &str,
        repo: &str,
        sha: &str,
        context: &str,
        state: &str,
        description: String,
        target_url: Option<String>,
    ) -> Result<(), ProviderError> {
        let body = CommitStatus {
            state,
            context,
            description,
            target_url,
        };

        match provider {
            ProviderKind::GitHub => {
                let token = self
                    .github_token
                    .as_ref()
                    .ok_or(ProviderError::MissingToken("GitHub"))?;
                let url = format!("https://api.github.com/repos/{owner}/{repo}/statuses/{sha}");
                self.post_json(&url, token, "Bearer", &body).await
            }
            ProviderKind::Gitea => {
                let token = self
                    .codeberg_token
                    .as_ref()
                    .ok_or(ProviderError::MissingToken("Codeberg/Gitea"))?;
                let url = format!("https://codeberg.org/api/v1/repos/{owner}/{repo}/statuses/{sha}");
                self.post_json(&url, token, "token", &body).await
            }
        }
    }

    pub async fn comment_on_pr(
        &self,
        provider: ProviderKind,
        owner: &str,
        repo: &str,
        pr_number: u64,
        body: &str,
    ) -> Result<(), ProviderError> {
        #[derive(Serialize)]
        struct Comment<'a> {
            body: &'a str,
        }

        match provider {
            ProviderKind::GitHub => {
                let token = self
                    .github_token
                    .as_ref()
                    .ok_or(ProviderError::MissingToken("GitHub"))?;
                let url =
                    format!("https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments");
                self.post_json(&url, token, "Bearer", &Comment { body }).await
            }
            ProviderKind::Gitea => {
                let token = self
                    .codeberg_token
                    .as_ref()
                    .ok_or(ProviderError::MissingToken("Codeberg/Gitea"))?;
                let url = format!(
                    "https://codeberg.org/api/v1/repos/{owner}/{repo}/issues/{pr_number}/comments"
                );
                self.post_json(&url, token, "token", &Comment { body }).await
            }
        }
    }

    pub async fn open_fix_pr(
        &self,
        provider: ProviderKind,
        owner: &str,
        repo: &str,
        head_branch: &str,
        base_branch: &str,
        title: &str,
        body: &str,
    ) -> Result<String, ProviderError> {
        #[derive(Serialize)]
        struct NewPr<'a> {
            title: &'a str,
            head: &'a str,
            base: &'a str,
            body: &'a str,
        }

        match provider {
            ProviderKind::GitHub => {
                let token = self
                    .github_token
                    .as_ref()
                    .ok_or(ProviderError::MissingToken("GitHub"))?;
                let url = format!("https://api.github.com/repos/{owner}/{repo}/pulls");
                let resp = self
                    .http
                    .post(&url)
                    .header("Authorization", format!("Bearer {token}"))
                    .header("Accept", "application/vnd.github+json")
                    .header("User-Agent", "compliance-as-code-agent")
                    .json(&NewPr {
                        title,
                        head: head_branch,
                        base: base_branch,
                        body,
                    })
                    .send()
                    .await?;
                let status = resp.status();
                let text = resp.text().await?;
                if !status.is_success() {
                    return Err(ProviderError::Api {
                        status: status.as_u16(),
                        body: text,
                    });
                }
                let json: serde_json::Value = serde_json::from_str(&text).unwrap_or_default();
                Ok(json["html_url"].as_str().unwrap_or("").to_string())
            }
            ProviderKind::Gitea => {
                let token = self
                    .codeberg_token
                    .as_ref()
                    .ok_or(ProviderError::MissingToken("Codeberg/Gitea"))?;
                let url = format!("https://codeberg.org/api/v1/repos/{owner}/{repo}/pulls");
                let resp = self
                    .http
                    .post(&url)
                    .header("Authorization", format!("token {token}"))
                    .header("User-Agent", "compliance-as-code-agent")
                    .json(&NewPr {
                        title,
                        head: head_branch,
                        base: base_branch,
                        body,
                    })
                    .send()
                    .await?;
                let status = resp.status();
                let text = resp.text().await?;
                if !status.is_success() {
                    return Err(ProviderError::Api {
                        status: status.as_u16(),
                        body: text,
                    });
                }
                let json: serde_json::Value = serde_json::from_str(&text).unwrap_or_default();
                Ok(json["html_url"].as_str().unwrap_or("").to_string())
            }
        }
    }

    async fn post_json<T: Serialize>(
        &self,
        url: &str,
        token: &str,
        auth_prefix: &str,
        body: &T,
    ) -> Result<(), ProviderError> {
        let resp = self
            .http
            .post(url)
            .header("Authorization", format!("{auth_prefix} {token}"))
            .header("Accept", "application/json")
            .header("User-Agent", "compliance-as-code-agent")
            .json(body)
            .send()
            .await?;
        let status = resp.status();
        if status.is_success() {
            Ok(())
        } else {
            Err(ProviderError::Api {
                status: status.as_u16(),
                body: resp.text().await.unwrap_or_default(),
            })
        }
    }
}
