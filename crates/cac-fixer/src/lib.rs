use cac_core::violation::{FixProposal, Violation};
use regex::Regex;
use std::path::{Path, PathBuf};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum FixError {
    #[error("io error: {0}")]
    Io(#[from] std::io::Error),
    #[error("no auto-fix available for rule {0}")]
    NotFixable(String),
}

pub struct Fixer {
    root: PathBuf,
    dry_run: bool,
}

impl Fixer {
    pub fn new(root: impl Into<PathBuf>, dry_run: bool) -> Self {
        Self {
            root: root.into(),
            dry_run,
        }
    }

    pub fn propose(&self, violations: &[Violation]) -> Vec<FixProposal> {
        violations
            .iter()
            .filter(|v| v.auto_fixable)
            .filter_map(|v| self.propose_for(v).ok())
            .collect()
    }

    pub fn apply(&self, proposals: &[FixProposal]) -> Result<usize, FixError> {
        let mut applied = 0usize;
        for proposal in proposals {
            if self.apply_one(proposal)? {
                applied += 1;
            }
        }
        Ok(applied)
    }

    fn propose_for(&self, violation: &Violation) -> Result<FixProposal, FixError> {
        match violation.rule_id.as_str() {
            id if id.starts_with("secret-") => self.propose_secret_fix(violation),
            id if id.starts_with("gdpr-") => self.propose_gdpr_fix(violation),
            id if id.starts_with("soc2-") => self.propose_soc2_fix(violation),
            _ => Err(FixError::NotFixable(violation.rule_id.clone())),
        }
    }

    fn propose_secret_fix(&self, violation: &Violation) -> Result<FixProposal, FixError> {
        let re = Regex::new(r#"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['"]?[^'"\s]+['"]?"#)
            .unwrap();
        let fixed = re.replace(
            &violation.snippet,
            "${1}=std::env::var(\"${1}\").expect(\"${1} must be set\")",
        );
        Ok(FixProposal {
            violation_id: format!("{}:{}", violation.file_path, violation.line),
            file_path: violation.file_path.clone(),
            original_snippet: violation.snippet.clone(),
            fixed_snippet: fixed.into_owned(),
            description: "Replace hardcoded secret with environment variable lookup".into(),
        })
    }

    fn propose_gdpr_fix(&self, violation: &Violation) -> Result<FixProposal, FixError> {
        let annotation = "/// @gdpr personal-data — requires lawful basis and retention policy\n";
        Ok(FixProposal {
            violation_id: format!("{}:{}", violation.file_path, violation.line),
            file_path: violation.file_path.clone(),
            original_snippet: violation.snippet.clone(),
            fixed_snippet: format!("{annotation}{}", violation.snippet),
            description: "Add GDPR data-classification annotation above PII field".into(),
        })
    }

    fn propose_soc2_fix(&self, violation: &Violation) -> Result<FixProposal, FixError> {
        Ok(FixProposal {
            violation_id: format!("{}:{}", violation.file_path, violation.line),
            file_path: violation.file_path.clone(),
            original_snippet: violation.snippet.clone(),
            fixed_snippet: format!(
                "audit_log::record(\"sensitive_operation\", &{{ \"file\": \"{}\", \"line\": {} }});",
                violation.file_path, violation.line
            ),
            description: "Insert SOC2 audit trail call for sensitive operation".into(),
        })
    }

    fn apply_one(&self, proposal: &FixProposal) -> Result<bool, FixError> {
        let path = self.root.join(&proposal.file_path);
        if !path.exists() {
            return Ok(false);
        }
        let content = std::fs::read_to_string(&path)?;
        if !content.contains(&proposal.original_snippet) {
            return Ok(false);
        }
        let updated = content.replace(
            &proposal.original_snippet,
            &proposal.fixed_snippet,
        );
        if self.dry_run {
            return Ok(true);
        }
        std::fs::write(path, updated)?;
        Ok(true)
    }
}

pub fn group_by_file(violations: &[Violation]) -> Vec<(String, Vec<&Violation>)> {
    let mut files: Vec<String> = violations
        .iter()
        .map(|v| v.file_path.clone())
        .collect();
    files.sort();
    files.dedup();
    files
        .into_iter()
        .map(|f| {
            let items: Vec<_> = violations.iter().filter(|v| v.file_path == f).collect();
            (f, items)
        })
        .collect()
}

pub fn root_path(root: &Path) -> PathBuf {
    root.to_path_buf()
}
