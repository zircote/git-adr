//! Export ADR metrics in JSON format.

use anyhow::Result;
use chrono::{Datelike, Utc};
use clap::Args as ClapArgs;
use colored::Colorize;
use std::collections::HashMap;
use std::fs;
use std::path::Path;

use crate::core::{ConfigManager, Git, NotesManager};

/// Arguments for the metrics command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// Output file (stdout if not specified).
    #[arg(long, short)]
    pub output: Option<String>,

    /// Include individual ADR metrics.
    #[arg(long)]
    pub include_adrs: bool,

    /// Pretty print JSON output.
    #[arg(long)]
    pub pretty: bool,
}

/// Run the metrics command.
///
/// # Errors
///
/// Returns an error if metrics export fails.
pub fn run(args: Args) -> Result<()> {
    let git = Git::new();
    git.check_repository()?;

    let config = ConfigManager::new(git.clone()).load()?;
    let notes = NotesManager::new(git, config.clone());

    let adrs = notes.list()?;

    // Collect metrics
    let mut status_counts: HashMap<String, usize> = HashMap::new();
    let mut tag_counts: HashMap<String, usize> = HashMap::new();
    let mut monthly_counts: HashMap<String, usize> = HashMap::new();
    let mut adr_metrics = Vec::new();

    for adr in &adrs {
        // Count by status
        *status_counts
            .entry(adr.frontmatter.status.to_string())
            .or_insert(0) += 1;

        // Count by tags
        for tag in &adr.frontmatter.tags {
            *tag_counts.entry(tag.clone()).or_insert(0) += 1;
        }

        // Count by month
        if let Some(date) = &adr.frontmatter.date {
            let month_key = format!("{}-{:02}", date.0.year(), date.0.month());
            *monthly_counts.entry(month_key).or_insert(0) += 1;
        }

        // Individual ADR metrics
        if args.include_adrs {
            adr_metrics.push(serde_json::json!({
                "id": adr.id,
                "title": adr.frontmatter.title,
                "status": adr.frontmatter.status.to_string(),
                "date": adr.frontmatter.date.as_ref().map(|d| d.0.to_rfc3339()),
                "tags": adr.frontmatter.tags,
                "authors": adr.frontmatter.authors,
                "commit": if adr.commit.is_empty() { None } else { Some(&adr.commit) },
            }));
        }
    }

    // Calculate derived metrics
    let accepted = status_counts.get("accepted").unwrap_or(&0);
    let rejected = status_counts.get("rejected").unwrap_or(&0);
    let deprecated = status_counts.get("deprecated").unwrap_or(&0);
    let superseded = status_counts.get("superseded").unwrap_or(&0);

    let total_decided = accepted + rejected + deprecated + superseded;
    #[allow(clippy::cast_precision_loss)]
    let acceptance_rate = if total_decided == 0 {
        100.0
    } else {
        (*accepted as f64 / total_decided as f64) * 100.0
    };

    #[allow(clippy::cast_precision_loss)]
    let churn_rate = if adrs.is_empty() {
        0.0
    } else {
        ((deprecated + superseded) as f64 / adrs.len() as f64) * 100.0
    };

    // Build metrics JSON
    let mut metrics = serde_json::json!({
        "metadata": {
            "generated_at": Utc::now().to_rfc3339(),
            "tool_version": env!("CARGO_PKG_VERSION"),
            "prefix": config.prefix,
        },
        "summary": {
            "total_adrs": adrs.len(),
            "acceptance_rate": format!("{:.1}", acceptance_rate),
            "churn_rate": format!("{:.1}", churn_rate),
        },
        "status_breakdown": status_counts,
        "tags": {
            "total_unique": tag_counts.len(),
            "counts": tag_counts,
        },
        "timeline": {
            "monthly_counts": monthly_counts,
            "first_adr_date": get_first_date(&adrs),
            "last_adr_date": get_last_date(&adrs),
        },
    });

    if args.include_adrs {
        metrics["adrs"] = serde_json::json!(adr_metrics);
    }

    let output = if args.pretty {
        serde_json::to_string_pretty(&metrics)?
    } else {
        serde_json::to_string(&metrics)?
    };

    if let Some(output_path) = args.output {
        let path = Path::new(&output_path);
        if let Some(parent) = path.parent() {
            if !parent.exists() {
                fs::create_dir_all(parent)?;
            }
        }
        fs::write(&output_path, &output)?;
        eprintln!(
            "{} Metrics exported to: {}",
            "✓".green(),
            output_path.cyan()
        );
    } else {
        println!("{output}");
    }

    Ok(())
}

/// Get the earliest ADR date.
fn get_first_date(adrs: &[crate::core::Adr]) -> Option<String> {
    adrs.iter()
        .filter_map(|a| a.frontmatter.date.as_ref())
        .min_by_key(|d| d.0)
        .map(|d| d.0.to_rfc3339())
}

/// Get the latest ADR date.
fn get_last_date(adrs: &[crate::core::Adr]) -> Option<String> {
    adrs.iter()
        .filter_map(|a| a.frontmatter.date.as_ref())
        .max_by_key(|d| d.0)
        .map(|d| d.0.to_rfc3339())
}
