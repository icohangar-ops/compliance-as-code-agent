use std::path::Path;

pub const DEFAULT_SKIP_DIRS: &[&str] = &[
    ".git",
    ".cac",
    "target",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "vendor",
];

pub fn should_skip_entry(path: &Path, root: &Path) -> bool {
    let rel = path.strip_prefix(root).unwrap_or(path);
    for component in rel.components() {
        if let Some(name) = component.as_os_str().to_str() {
            if DEFAULT_SKIP_DIRS.contains(&name) {
                return true;
            }
        }
    }
    false
}

pub fn is_binary_or_large(path: &Path, max_size: u64) -> bool {
    if let Ok(meta) = std::fs::metadata(path) {
        if meta.len() > max_size {
            return true;
        }
    }
    let ext = path
        .extension()
        .and_then(|e| e.to_str())
        .unwrap_or("")
        .to_lowercase();
    matches!(
        ext.as_str(),
        "png" | "jpg" | "jpeg" | "gif" | "webp" | "ico" | "pdf" | "zip" | "gz" | "wasm" | "exe" | "dll" | "so" | "dylib" | "lock"
    )
}

pub fn is_likely_false_positive(line: &str, matched: &str) -> bool {
    let lower = line.to_lowercase();
    if lower.contains("example")
        || lower.contains("placeholder")
        || lower.contains("changeme")
        || lower.contains("your_")
        || lower.contains("xxx")
        || lower.contains("redacted")
    {
        return true;
    }
    if matched.len() < 8 && !matched.contains('=') {
        return true;
    }
    false
}
