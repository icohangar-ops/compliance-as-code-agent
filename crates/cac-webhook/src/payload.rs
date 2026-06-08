use serde::Deserialize;

#[derive(Debug, Clone, Deserialize)]
pub struct PullRequestEvent {
    pub action: String,
    pub number: Option<u64>,
    pub pull_request: Option<PullRequest>,
    pub repository: Repository,
}

#[derive(Debug, Clone, Deserialize)]
pub struct PullRequest {
    pub number: u64,
    pub head: GitRef,
    pub base: GitRef,
    pub html_url: Option<String>,
    pub title: Option<String>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct GitRef {
    pub sha: String,
    pub r#ref: String,
    #[serde(default)]
    pub repo: Option<HeadRepo>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct HeadRepo {
    pub clone_url: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct Repository {
    pub full_name: String,
    pub clone_url: String,
    pub html_url: Option<String>,
    pub owner: Owner,
    pub name: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct Owner {
    pub login: String,
}

#[derive(Debug, Clone)]
pub struct PrContext {
    pub provider: ProviderKind,
    pub action: String,
    pub owner: String,
    pub repo: String,
    pub pr_number: u64,
    pub head_sha: String,
    pub head_ref: String,
    pub base_ref: String,
    pub clone_url: String,
    pub head_clone_url: String,
    pub pr_url: Option<String>,
    pub title: Option<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProviderKind {
    GitHub,
    Gitea,
}

impl PullRequestEvent {
    pub fn into_context(self, provider: ProviderKind) -> Option<PrContext> {
        if !is_action_supported(&self.action) {
            return None;
        }
        let pr = self.pull_request?;
        let clone_url = self.repository.clone_url;
        Some(PrContext {
            provider,
            action: self.action,
            owner: self.repository.owner.login,
            repo: self.repository.name,
            pr_number: pr.number,
            head_sha: pr.head.sha,
            head_ref: pr.head.r#ref,
            base_ref: pr.base.r#ref,
            head_clone_url: pr
                .head
                .repo
                .as_ref()
                .map(|r| r.clone_url.clone())
                .unwrap_or_else(|| clone_url.clone()),
            clone_url,
            pr_url: pr.html_url,
            title: pr.title,
        })
    }
}

fn is_action_supported(action: &str) -> bool {
    matches!(action, "opened" | "synchronize" | "reopened" | "edited")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_opened_pull_request() {
        let body = r#"{
            "action": "opened",
            "pull_request": {
                "number": 42,
                "head": { "sha": "abc123", "ref": "feature" },
                "base": { "sha": "def456", "ref": "main" },
                "html_url": "https://github.com/org/repo/pull/42"
            },
            "repository": {
                "full_name": "org/repo",
                "name": "repo",
                "clone_url": "https://github.com/org/repo.git",
                "owner": { "login": "org" }
            }
        }"#;
        let event: PullRequestEvent = serde_json::from_str(body).unwrap();
        let ctx = event.into_context(ProviderKind::GitHub).unwrap();
        assert_eq!(ctx.pr_number, 42);
        assert_eq!(ctx.head_sha, "abc123");
        assert_eq!(ctx.base_ref, "main");
    }

    #[test]
    fn ignores_closed_action() {
        let body = r#"{
            "action": "closed",
            "pull_request": {
                "number": 1,
                "head": { "sha": "a", "ref": "b" },
                "base": { "sha": "c", "ref": "main" }
            },
            "repository": {
                "full_name": "o/r",
                "name": "r",
                "clone_url": "https://example.com/o/r.git",
                "owner": { "login": "o" }
            }
        }"#;
        let event: PullRequestEvent = serde_json::from_str(body).unwrap();
        assert!(event.into_context(ProviderKind::GitHub).is_none());
    }
}
