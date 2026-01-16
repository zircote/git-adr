//! Generate ADR analytics reports.

use anyhow::Result;
use chrono::{Datelike, Utc};
use clap::Args as ClapArgs;
use colored::Colorize;
use std::collections::HashMap;
use std::fmt::Write as _;
use std::fs;
use std::path::Path;

use crate::core::{AdrStatus, ConfigManager, Git, NotesManager};

/// Arguments for the report command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// Output format (markdown, html, json).
    #[arg(long, short, default_value = "markdown")]
    pub format: String,

    /// Output file (stdout if not specified).
    #[arg(long, short)]
    pub output: Option<String>,

    /// Include detailed status breakdown.
    #[arg(long)]
    pub detailed: bool,

    /// Include timeline analysis.
    #[arg(long)]
    pub timeline: bool,
}

/// Run the report command.
///
/// # Errors
///
/// Returns an error if report generation fails.
pub fn run(args: Args) -> Result<()> {
    let git = Git::new();
    git.check_repository()?;

    let config = ConfigManager::new(git.clone()).load()?;
    let notes = NotesManager::new(git, config);

    let adrs = notes.list()?;

    if adrs.is_empty() {
        eprintln!(
            "{} No ADRs found. Create your first ADR with: git adr new <title>",
            "→".yellow()
        );
        return Ok(());
    }

    // Collect statistics
    let mut status_counts: HashMap<AdrStatus, usize> = HashMap::new();
    let mut tag_counts: HashMap<String, usize> = HashMap::new();
    let mut monthly_counts: HashMap<String, usize> = HashMap::new();

    for adr in &adrs {
        // Count by status
        *status_counts
            .entry(adr.frontmatter.status.clone())
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
    }

    let report = match args.format.as_str() {
        "json" => generate_json_report(&adrs, &status_counts, &tag_counts, &monthly_counts)?,
        "html" => generate_html_report(
            &adrs,
            &status_counts,
            &tag_counts,
            &monthly_counts,
            args.detailed,
            args.timeline,
        ),
        _ => generate_markdown_report(
            &adrs,
            &status_counts,
            &tag_counts,
            &monthly_counts,
            args.detailed,
            args.timeline,
        ),
    };

    if let Some(output_path) = args.output {
        let path = Path::new(&output_path);
        if let Some(parent) = path.parent() {
            if !parent.exists() {
                fs::create_dir_all(parent)?;
            }
        }
        fs::write(&output_path, &report)?;
        eprintln!("{} Report saved to: {}", "✓".green(), output_path.cyan());
    } else {
        println!("{report}");
    }

    Ok(())
}

/// Generate JSON report.
fn generate_json_report(
    adrs: &[crate::core::Adr],
    status_counts: &HashMap<AdrStatus, usize>,
    tag_counts: &HashMap<String, usize>,
    monthly_counts: &HashMap<String, usize>,
) -> Result<String> {
    let mut status_map: HashMap<String, usize> = HashMap::new();
    for (status, count) in status_counts {
        status_map.insert(status.to_string(), *count);
    }

    let report = serde_json::json!({
        "generated_at": Utc::now().to_rfc3339(),
        "total_adrs": adrs.len(),
        "status_breakdown": status_map,
        "tag_breakdown": tag_counts,
        "monthly_breakdown": monthly_counts,
        "acceptance_rate": calculate_acceptance_rate(status_counts),
    });

    Ok(serde_json::to_string_pretty(&report)?)
}

/// Generate markdown report.
#[allow(clippy::cast_precision_loss)]
fn generate_markdown_report(
    adrs: &[crate::core::Adr],
    status_counts: &HashMap<AdrStatus, usize>,
    tag_counts: &HashMap<String, usize>,
    monthly_counts: &HashMap<String, usize>,
    detailed: bool,
    timeline: bool,
) -> String {
    let mut report = String::new();

    report.push_str("# Architecture Decision Records Report\n\n");
    let _ = writeln!(
        report,
        "*Generated: {}*\n",
        Utc::now().format("%Y-%m-%d %H:%M UTC")
    );

    // Summary
    report.push_str("## Summary\n\n");
    let _ = writeln!(report, "- **Total ADRs**: {}", adrs.len());
    let _ = writeln!(
        report,
        "- **Acceptance Rate**: {:.1}%\n",
        calculate_acceptance_rate(status_counts)
    );

    // Status breakdown
    report.push_str("## Status Breakdown\n\n");
    report.push_str("| Status | Count | Percentage |\n");
    report.push_str("|--------|-------|------------|\n");

    let statuses = [
        AdrStatus::Proposed,
        AdrStatus::Accepted,
        AdrStatus::Deprecated,
        AdrStatus::Superseded,
        AdrStatus::Rejected,
    ];

    for status in &statuses {
        let count = status_counts.get(status).unwrap_or(&0);
        let percentage = if adrs.is_empty() {
            0.0
        } else {
            (*count as f64 / adrs.len() as f64) * 100.0
        };
        let _ = writeln!(report, "| {} | {} | {:.1}% |", status, count, percentage);
    }
    report.push('\n');

    // Top tags
    if !tag_counts.is_empty() {
        report.push_str("## Top Tags\n\n");
        let mut tags: Vec<_> = tag_counts.iter().collect();
        tags.sort_by(|a, b| b.1.cmp(a.1));

        for (tag, count) in tags.iter().take(10) {
            let _ = writeln!(report, "- `{}`: {} ADRs", tag, count);
        }
        report.push('\n');
    }

    // Timeline
    if timeline && !monthly_counts.is_empty() {
        report.push_str("## Timeline\n\n");
        let mut months: Vec<_> = monthly_counts.iter().collect();
        months.sort_by(|a, b| a.0.cmp(b.0));

        report.push_str("| Month | ADRs Created |\n");
        report.push_str("|-------|-------------|\n");
        for (month, count) in months {
            let _ = writeln!(report, "| {} | {} |", month, count);
        }
        report.push('\n');
    }

    // Detailed list
    if detailed {
        report.push_str("## ADR List\n\n");
        report.push_str("| ID | Title | Status | Date |\n");
        report.push_str("|-----|-------|--------|------|\n");

        for adr in adrs {
            let date = adr
                .frontmatter
                .date
                .as_ref()
                .map_or_else(|| "-".to_string(), |d| d.0.format("%Y-%m-%d").to_string());
            let _ = writeln!(
                report,
                "| {} | {} | {} | {} |",
                adr.id, adr.frontmatter.title, adr.frontmatter.status, date
            );
        }
    }

    report
}

/// Generate HTML report.
#[allow(clippy::cast_precision_loss, clippy::too_many_lines)]
fn generate_html_report(
    adrs: &[crate::core::Adr],
    status_counts: &HashMap<AdrStatus, usize>,
    tag_counts: &HashMap<String, usize>,
    monthly_counts: &HashMap<String, usize>,
    detailed: bool,
    timeline: bool,
) -> String {
    let mut html = String::new();

    html.push_str(r#"<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ADR Report</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }
        h1 { color: #333; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        table { border-collapse: collapse; width: 100%; margin: 15px 0; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        th { background: #f5f5f5; }
        tr:hover { background: #fafafa; }
        .stat { display: inline-block; padding: 15px 25px; margin: 5px; background: #f0f7ff; border-radius: 8px; }
        .stat-value { font-size: 28px; font-weight: bold; color: #0066cc; }
        .stat-label { font-size: 12px; color: #666; text-transform: uppercase; }
        .tag { display: inline-block; padding: 2px 8px; margin: 2px; background: #e0e0e0; border-radius: 4px; font-size: 12px; }
        .status-proposed { color: #f59e0b; }
        .status-accepted { color: #10b981; }
        .status-deprecated { color: #6b7280; }
        .status-superseded { color: #8b5cf6; }
        .status-rejected { color: #ef4444; }
    </style>
</head>
<body>
"#);

    html.push_str("<h1>Architecture Decision Records Report</h1>\n");
    let _ = writeln!(
        html,
        "<p><em>Generated: {}</em></p>",
        Utc::now().format("%Y-%m-%d %H:%M UTC")
    );

    // Summary stats
    html.push_str("<div>\n");
    let _ = write!(
        html,
        r#"<div class="stat"><div class="stat-value">{}</div><div class="stat-label">Total ADRs</div></div>"#,
        adrs.len()
    );
    let _ = write!(
        html,
        r#"<div class="stat"><div class="stat-value">{:.0}%</div><div class="stat-label">Acceptance Rate</div></div>"#,
        calculate_acceptance_rate(status_counts)
    );
    html.push_str("</div>\n\n");

    // Status breakdown
    html.push_str("<h2>Status Breakdown</h2>\n<table>\n<tr><th>Status</th><th>Count</th><th>Percentage</th></tr>\n");
    for status in &[
        AdrStatus::Proposed,
        AdrStatus::Accepted,
        AdrStatus::Deprecated,
        AdrStatus::Superseded,
        AdrStatus::Rejected,
    ] {
        let count = status_counts.get(status).unwrap_or(&0);
        let pct = if adrs.is_empty() {
            0.0
        } else {
            (*count as f64 / adrs.len() as f64) * 100.0
        };
        let class = format!("status-{}", status.to_string().to_lowercase());
        let _ = writeln!(
            html,
            r#"<tr><td class="{}">{}</td><td>{}</td><td>{:.1}%</td></tr>"#,
            class, status, count, pct
        );
    }
    html.push_str("</table>\n\n");

    // Tags
    if !tag_counts.is_empty() {
        html.push_str("<h2>Top Tags</h2>\n<p>");
        let mut tags: Vec<_> = tag_counts.iter().collect();
        tags.sort_by(|a, b| b.1.cmp(a.1));
        for (tag, count) in tags.iter().take(15) {
            let _ = write!(html, r#"<span class="tag">{} ({})</span> "#, tag, count);
        }
        html.push_str("</p>\n\n");
    }

    // Timeline
    if timeline && !monthly_counts.is_empty() {
        html.push_str("<h2>Timeline</h2>\n<table>\n<tr><th>Month</th><th>ADRs Created</th></tr>\n");
        let mut months: Vec<_> = monthly_counts.iter().collect();
        months.sort_by(|a, b| a.0.cmp(b.0));
        for (month, count) in months {
            let _ = writeln!(html, "<tr><td>{}</td><td>{}</td></tr>", month, count);
        }
        html.push_str("</table>\n\n");
    }

    // Detailed list
    if detailed {
        html.push_str("<h2>ADR List</h2>\n<table>\n<tr><th>ID</th><th>Title</th><th>Status</th><th>Date</th></tr>\n");
        for adr in adrs {
            let date = adr
                .frontmatter
                .date
                .as_ref()
                .map_or_else(|| "-".to_string(), |d| d.0.format("%Y-%m-%d").to_string());
            let class = format!(
                "status-{}",
                adr.frontmatter.status.to_string().to_lowercase()
            );
            let _ = writeln!(
                html,
                r#"<tr><td>{}</td><td>{}</td><td class="{}">{}</td><td>{}</td></tr>"#,
                adr.id, adr.frontmatter.title, class, adr.frontmatter.status, date
            );
        }
        html.push_str("</table>\n");
    }

    html.push_str("</body>\n</html>");
    html
}

/// Calculate acceptance rate.
#[allow(clippy::cast_precision_loss)]
fn calculate_acceptance_rate(status_counts: &HashMap<AdrStatus, usize>) -> f64 {
    let accepted = *status_counts.get(&AdrStatus::Accepted).unwrap_or(&0);
    let total_decided = accepted
        + status_counts.get(&AdrStatus::Rejected).unwrap_or(&0)
        + status_counts.get(&AdrStatus::Deprecated).unwrap_or(&0)
        + status_counts.get(&AdrStatus::Superseded).unwrap_or(&0);

    if total_decided == 0 {
        100.0
    } else {
        (accepted as f64 / total_decided as f64) * 100.0
    }
}
