use anyhow::{Context, Result};
use cac_core::{
    audit::{default_ledger_path, AuditLedger, AuditPhase, LedgerConfig},
    violation::ScanReport,
};
use cac_fixer::Fixer;
use cac_scanner::{ScanConfig, Scanner};
use cac_validator::Validator;
use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser)]
#[command(
    name = "cac",
    about = "Compliance-as-Code Agent — scan, fix, and validate codebases against organizational policies",
    version
)]
struct Cli {
    #[command(subcommand)]
    command: Commands,

    #[command(flatten)]
    globals: GlobalOpts,
}

#[derive(Parser)]
struct GlobalOpts {
    /// Repository root to scan
    #[arg(long, global = true, default_value = ".")]
    root: PathBuf,

    /// Directory containing policy YAML files
    #[arg(long, global = true, default_value = "policies")]
    policies: PathBuf,

    /// HMAC signing key for audit ledger (or set CAC_LEDGER_SIGNING_KEY)
    #[arg(long, global = true, env = "CAC_LEDGER_SIGNING_KEY")]
    signing_key: Option<String>,

    /// Output format: json or text
    #[arg(long, global = true, default_value = "text")]
    format: String,
}

#[derive(Subcommand)]
enum Commands {
    /// Detector agent: scan codebase for policy violations
    Scan,
    /// Fixer agent: propose and apply auto-fixes
    Fix {
        /// Preview fixes without writing files
        #[arg(long)]
        dry_run: bool,
    },
    /// Validator agent: re-scan and adversarially validate fixes
    Validate {
        /// Number of fixes applied in prior step
        #[arg(long, default_value_t = 0)]
        fixes_applied: usize,
    },
    /// Full pipeline: detect → fix → validate
    Run {
        #[arg(long)]
        dry_run: bool,
    },
    /// Show signed audit trail
    Audit,
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    let ledger = build_ledger(&cli.globals)?;

    match cli.command {
        Commands::Scan => {
            let report = scan(&cli.globals)?;
            ledger.record(
                AuditPhase::Detect,
                "detector-agent",
                "scan_complete",
                None,
                None,
                None,
                serde_json::json!({
                    "violations": report.violation_count(),
                    "files_scanned": report.files_scanned,
                }),
            )?;
            emit_scan(&cli.globals.format, &report)?;
            if report.has_critical() {
                std::process::exit(1);
            }
        }
        Commands::Fix { dry_run } => {
            let report = scan(&cli.globals)?;
            let fixer = Fixer::new(&cli.globals.root, dry_run);
            let proposals = fixer.propose(&report.violations);
            let applied = fixer.apply(&proposals)?;
            ledger.record(
                AuditPhase::Fix,
                "fixer-agent",
                if dry_run { "dry_run" } else { "apply_fixes" },
                None,
                None,
                None,
                serde_json::json!({
                    "proposed": proposals.len(),
                    "applied": applied,
                    "dry_run": dry_run,
                }),
            )?;
            if cli.globals.format == "json" {
                println!("{}", serde_json::to_string_pretty(&proposals)?);
            } else {
                println!("Proposed {} fix(es), applied {}", proposals.len(), applied);
                for p in &proposals {
                    println!("  [{}] {} — {}", p.file_path, p.description, p.fixed_snippet);
                }
            }
        }
        Commands::Validate { fixes_applied } => {
            let original = scan(&cli.globals)?;
            let validator = Validator::new(&cli.globals.root, &cli.globals.policies);
            let report = validator.validate_after_fix(&original, fixes_applied)?;
            ledger.record(
                AuditPhase::Validate,
                "validator-agent",
                if report.passed { "passed" } else { "failed" },
                None,
                None,
                None,
                serde_json::json!({
                    "original": report.original_violations,
                    "remaining": report.remaining_violations,
                    "fixes_applied": report.fixes_applied,
                    "adversarial_notes": report.adversarial_notes,
                }),
            )?;
            if cli.globals.format == "json" {
                println!("{}", serde_json::to_string_pretty(&report)?);
            } else {
                println!(
                    "Validation {} — {}/{} violations remain after {} fix(es)",
                    if report.passed { "PASSED" } else { "FAILED" },
                    report.remaining_violations,
                    report.original_violations,
                    report.fixes_applied
                );
                for note in &report.adversarial_notes {
                    println!("  • {note}");
                }
            }
            if !report.passed {
                std::process::exit(1);
            }
        }
        Commands::Run { dry_run } => {
            let original = scan(&cli.globals)?;
            ledger.record(
                AuditPhase::Detect,
                "detector-agent",
                "scan_complete",
                None,
                None,
                None,
                serde_json::json!({ "violations": original.violation_count() }),
            )?;

            let fixer = Fixer::new(&cli.globals.root, dry_run);
            let proposals = fixer.propose(&original.violations);
            let applied = fixer.apply(&proposals)?;
            ledger.record(
                AuditPhase::Fix,
                "fixer-agent",
                "apply_fixes",
                None,
                None,
                None,
                serde_json::json!({ "proposed": proposals.len(), "applied": applied }),
            )?;

            let validator = Validator::new(&cli.globals.root, &cli.globals.policies);
            let validation = validator.validate_after_fix(&original, applied)?;
            ledger.record(
                AuditPhase::Validate,
                "validator-agent",
                if validation.passed { "passed" } else { "failed" },
                None,
                None,
                None,
                serde_json::json!({
                    "remaining": validation.remaining_violations,
                    "passed": validation.passed,
                }),
            )?;

            if cli.globals.format == "json" {
                println!(
                    "{}",
                    serde_json::to_string_pretty(&serde_json::json!({
                        "scan": original,
                        "fixes_applied": applied,
                        "validation": validation,
                    }))?
                );
            } else {
                println!("=== Compliance-as-Code Pipeline ===");
                println!("Detect: {} violation(s) in {} file(s)", original.violation_count(), original.files_scanned);
                println!("Fix:    {} proposal(s), {} applied", proposals.len(), applied);
                println!(
                    "Validate: {} — {} remaining",
                    if validation.passed { "PASSED" } else { "FAILED" },
                    validation.remaining_violations
                );
            }
            if !validation.passed {
                std::process::exit(1);
            }
        }
        Commands::Audit => {
            let events = ledger.read_all()?;
            if cli.globals.format == "json" {
                println!("{}", serde_json::to_string_pretty(&events)?);
            } else {
                println!("Audit trail ({} events):", events.len());
                for e in events {
                    println!(
                        "  [{}] {:?} {} — {} ({})",
                        e.timestamp, e.phase, e.agent, e.action, e.id
                    );
                }
            }
        }
    }

    Ok(())
}

fn build_ledger(opts: &GlobalOpts) -> Result<AuditLedger> {
    Ok(AuditLedger::new(LedgerConfig {
        signing_key: opts.signing_key.clone(),
        ledger_path: default_ledger_path(&opts.root),
    }))
}

fn scan(opts: &GlobalOpts) -> Result<ScanReport> {
    let scanner = Scanner::from_config(ScanConfig::new(&opts.root, &opts.policies))
        .context("failed to initialize scanner")?;
    scanner.scan().context("scan failed")
}

fn emit_scan(format: &str, report: &ScanReport) -> Result<()> {
    if format == "json" {
        println!("{}", serde_json::to_string_pretty(report)?);
    } else if report.violations.is_empty() {
        println!(
            "No violations found ({} files scanned)",
            report.files_scanned
        );
    } else {
        println!(
            "Found {} violation(s) across {} files scanned:\n",
            report.violations.len(),
            report.files_scanned
        );
        for v in &report.violations {
            println!(
                "[{:?}] {}:{} — {} ({})",
                v.severity, v.file_path, v.line, v.message, v.rule_id
            );
            println!("    {}", v.snippet);
        }
    }
    Ok(())
}
