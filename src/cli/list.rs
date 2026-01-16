//! List all ADRs.

use anyhow::Result;
use chrono::{DateTime, NaiveDate, Utc};
use clap::Args as ClapArgs;
use colored::Colorize;

use crate::core::{Adr, AdrStatus, ConfigManager, Git, NotesManager};

/// Arguments for the list command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// Filter by status.
    #[arg(long, short)]
    pub status: Option<String>,

    /// Filter by tag.
    #[arg(long, short = 'g')]
    pub tag: Option<String>,

    /// Filter by date (since).
    #[arg(long)]
    pub since: Option<String>,

    /// Filter by date (until).
    #[arg(long)]
    pub until: Option<String>,

    /// Output format (table, json, csv, oneline).
    #[arg(long, short, default_value = "table")]
    pub format: String,

    /// Reverse sort order.
    #[arg(long, short)]
    pub reverse: bool,
}

/// Run the list command.
///
/// # Errors
///
/// Returns an error if listing fails.
pub fn run(args: Args) -> Result<()> {
    // Initialize git and load config
    let git = Git::new();
    git.check_repository()?;

    let config = ConfigManager::new(git.clone()).load()?;
    let notes = NotesManager::new(git, config);

    // Get all ADRs
    let mut adrs = notes.list()?;

    // Apply filters
    if let Some(status_filter) = &args.status {
        let target_status: AdrStatus = status_filter
            .parse()
            .map_err(|e| anyhow::anyhow!("{}", e))?;
        adrs.retain(|adr| *adr.status() == target_status);
    }

    if let Some(tag_filter) = &args.tag {
        adrs.retain(|adr| adr.has_tag(tag_filter));
    }

    if let Some(since) = &args.since {
        let since_date = parse_date(since)?;
        adrs.retain(|adr| {
            adr.frontmatter
                .date
                .as_ref()
                .is_none_or(|d| d.datetime() >= since_date)
        });
    }

    if let Some(until) = &args.until {
        let until_date = parse_date(until)?;
        adrs.retain(|adr| {
            adr.frontmatter
                .date
                .as_ref()
                .is_none_or(|d| d.datetime() <= until_date)
        });
    }

    // Apply sort order
    if args.reverse {
        adrs.reverse();
    }

    // Check if empty
    if adrs.is_empty() {
        eprintln!(
            "{} No ADRs found. Create one with: git adr new \"Title\"",
            "→".yellow()
        );
        return Ok(());
    }

    // Format output
    match args.format.as_str() {
        "json" => print_json(&adrs)?,
        "csv" => print_csv(&adrs),
        "oneline" => print_oneline(&adrs),
        _ => print_table(&adrs),
    }

    Ok(())
}

/// Parse a date string into a DateTime.
fn parse_date(s: &str) -> Result<DateTime<Utc>> {
    // Try ISO 8601 format first
    if let Ok(dt) = DateTime::parse_from_rfc3339(s) {
        return Ok(dt.with_timezone(&Utc));
    }

    // Try YYYY-MM-DD format
    if let Ok(date) = NaiveDate::parse_from_str(s, "%Y-%m-%d") {
        return Ok(date.and_hms_opt(0, 0, 0).unwrap().and_utc());
    }

    Err(anyhow::anyhow!(
        "Invalid date format: {}. Use YYYY-MM-DD or RFC3339.",
        s
    ))
}

/// Print ADRs as a table.
fn print_table(adrs: &[Adr]) {
    // Calculate column widths
    let id_width = adrs.iter().map(|a| a.id.len()).max().unwrap_or(10).max(4);
    let status_width = adrs
        .iter()
        .map(|a| a.status().to_string().len())
        .max()
        .unwrap_or(10)
        .max(6);
    let title_width = 50;

    // Print header
    println!(
        "{:id_width$}  {:status_width$}  {}",
        "ID".bold(),
        "STATUS".bold(),
        "TITLE".bold()
    );
    println!(
        "{:-<id_width$}  {:-<status_width$}  {:-<title_width$}",
        "", "", ""
    );

    // Print rows
    for adr in adrs {
        let status_str = adr.status().to_string();
        let status_colored = match adr.status() {
            AdrStatus::Proposed => status_str.yellow(),
            AdrStatus::Accepted => status_str.green(),
            AdrStatus::Deprecated => status_str.dimmed(),
            AdrStatus::Superseded => status_str.magenta(),
            AdrStatus::Rejected => status_str.red(),
        };

        let title = if adr.title().len() > title_width {
            format!("{}...", &adr.title()[..title_width - 3])
        } else {
            adr.title().to_string()
        };

        println!(
            "{:id_width$}  {:status_width$}  {}",
            adr.id.cyan(),
            status_colored,
            title
        );
    }

    println!();
    println!("{} ADR(s) found", adrs.len().to_string().bold());
}

/// Print ADRs as JSON.
fn print_json(adrs: &[Adr]) -> Result<()> {
    let output: Vec<serde_json::Value> = adrs
        .iter()
        .map(|adr| {
            serde_json::json!({
                "id": adr.id,
                "title": adr.title(),
                "status": adr.status().to_string(),
                "date": adr.frontmatter.date.as_ref().map(|d| d.datetime().to_rfc3339()),
                "tags": adr.frontmatter.tags,
                "commit": adr.commit,
            })
        })
        .collect();

    println!("{}", serde_json::to_string_pretty(&output)?);
    Ok(())
}

/// Print ADRs as CSV.
fn print_csv(adrs: &[Adr]) {
    println!("id,status,title,date,tags,commit");
    for adr in adrs {
        let date = adr
            .frontmatter
            .date
            .as_ref()
            .map(|d| d.datetime().format("%Y-%m-%d").to_string())
            .unwrap_or_default();
        let tags = adr.frontmatter.tags.join(";");
        // Escape title for CSV (double quotes)
        let title = adr.title().replace('"', "\"\"");
        println!(
            "\"{}\",\"{}\",\"{}\",\"{}\",\"{}\",\"{}\"",
            adr.id,
            adr.status(),
            title,
            date,
            tags,
            adr.commit
        );
    }
}

/// Print ADRs in one-line format.
fn print_oneline(adrs: &[Adr]) {
    for adr in adrs {
        let status = match adr.status() {
            AdrStatus::Proposed => "[P]".yellow(),
            AdrStatus::Accepted => "[A]".green(),
            AdrStatus::Deprecated => "[D]".dimmed(),
            AdrStatus::Superseded => "[S]".magenta(),
            AdrStatus::Rejected => "[R]".red(),
        };
        println!("{} {} {}", adr.id.cyan(), status, adr.title());
    }
}
