//! Show ADR statistics.

use anyhow::Result;
use clap::Args as ClapArgs;
use colored::Colorize;
use std::collections::HashMap;

use crate::core::{AdrStatus, ConfigManager, Git, NotesManager};

/// Arguments for the stats command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// Output format (text, json).
    #[arg(long, short, default_value = "text")]
    pub format: String,
}

/// Run the stats command.
///
/// # Errors
///
/// Returns an error if stats fails.
pub fn run(args: Args) -> Result<()> {
    let git = Git::new();
    git.check_repository()?;

    let config = ConfigManager::new(git.clone()).load()?;
    let notes = NotesManager::new(git, config);

    let adrs = notes.list()?;

    // Calculate statistics
    let total = adrs.len();

    // Count by status
    let mut by_status: HashMap<AdrStatus, usize> = HashMap::new();
    for adr in &adrs {
        *by_status.entry(adr.frontmatter.status.clone()).or_insert(0) += 1;
    }

    // Count by tag
    let mut by_tag: HashMap<String, usize> = HashMap::new();
    for adr in &adrs {
        for tag in &adr.frontmatter.tags {
            *by_tag.entry(tag.clone()).or_insert(0) += 1;
        }
    }

    // Find date range
    let dates: Vec<_> = adrs
        .iter()
        .filter_map(|a| a.frontmatter.date.as_ref())
        .collect();
    let oldest = dates.iter().min_by_key(|d| d.datetime());
    let newest = dates.iter().max_by_key(|d| d.datetime());

    if args.format.as_str() == "json" {
        let stats = serde_json::json!({
            "total": total,
            "by_status": by_status.iter()
                .map(|(k, v)| (k.to_string(), *v))
                .collect::<HashMap<_, _>>(),
            "by_tag": by_tag,
            "date_range": {
                "oldest": oldest.map(|d| d.datetime().to_rfc3339()),
                "newest": newest.map(|d| d.datetime().to_rfc3339()),
            }
        });
        println!("{}", serde_json::to_string_pretty(&stats)?);
    } else {
            println!("{}", "ADR Statistics".bold().underline());
            println!();
            println!("{} {}", "Total ADRs:".bold(), total.to_string().cyan());
            println!();

            // Status breakdown
            println!("{}", "By Status:".bold());
            let statuses = [
                AdrStatus::Proposed,
                AdrStatus::Accepted,
                AdrStatus::Rejected,
                AdrStatus::Deprecated,
                AdrStatus::Superseded,
            ];
            for status in &statuses {
                let count = by_status.get(status).unwrap_or(&0);
                let bar = "█".repeat(*count);
                println!(
                    "  {:12} {} {}",
                    status.to_string(),
                    count.to_string().cyan(),
                    bar.green()
                );
            }
            println!();

            // Tag breakdown (top 10)
            if !by_tag.is_empty() {
                println!("{}", "Top Tags:".bold());
                let mut tags: Vec<_> = by_tag.into_iter().collect();
                tags.sort_by(|a, b| b.1.cmp(&a.1));
                for (tag, count) in tags.iter().take(10) {
                    println!("  {} {}", tag.cyan(), count);
                }
                println!();
            }

            // Date range
            if let (Some(old), Some(new)) = (oldest, newest) {
                println!("{}", "Date Range:".bold());
                println!(
                    "  {} {} to {}",
                    "From:".dimmed(),
                    old.datetime().format("%Y-%m-%d"),
                    new.datetime().format("%Y-%m-%d")
                );
        }
    }

    Ok(())
}
