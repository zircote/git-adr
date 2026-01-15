//! Search ADRs.

use anyhow::Result;
use clap::Args as ClapArgs;
use colored::Colorize;
use regex::Regex;

use crate::core::{AdrStatus, ConfigManager, Git, NotesManager};

/// Arguments for the search command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// Search query.
    pub query: String,

    /// Filter by status.
    #[arg(long, short)]
    pub status: Option<String>,

    /// Filter by tag.
    #[arg(long, short = 'g')]
    pub tag: Option<String>,

    /// Case sensitive search.
    #[arg(long, short)]
    pub case_sensitive: bool,

    /// Use regex pattern.
    #[arg(long, short = 'E')]
    pub regex: bool,

    /// Context lines to show.
    #[arg(long, short = 'C', default_value = "2")]
    pub context: usize,

    /// Maximum results.
    #[arg(long)]
    pub limit: Option<usize>,
}

/// A search match result.
struct SearchMatch {
    line_number: usize,
    line: String,
    context_before: Vec<String>,
    context_after: Vec<String>,
}

/// Run the search command.
///
/// # Errors
///
/// Returns an error if search fails.
pub fn run(args: Args) -> Result<()> {
    let git = Git::new();
    git.check_repository()?;

    let config = ConfigManager::new(git.clone()).load()?;
    let notes = NotesManager::new(git, config);

    let mut adrs = notes.list()?;

    // Filter by status
    if let Some(status_str) = &args.status {
        let status: AdrStatus = status_str
            .parse()
            .map_err(|e| anyhow::anyhow!("{}", e))?;
        adrs.retain(|a| a.frontmatter.status == status);
    }

    // Filter by tag
    if let Some(tag) = &args.tag {
        adrs.retain(|a| a.frontmatter.tags.iter().any(|t| t.contains(tag)));
    }

    // Build search pattern
    let pattern = if args.regex {
        if args.case_sensitive {
            Regex::new(&args.query)?
        } else {
            Regex::new(&format!("(?i){}", &args.query))?
        }
    } else {
        let escaped = regex::escape(&args.query);
        if args.case_sensitive {
            Regex::new(&escaped)?
        } else {
            Regex::new(&format!("(?i){}", escaped))?
        }
    };

    let mut total_matches = 0;
    let mut results = Vec::new();

    for adr in &adrs {
        let content = adr.to_markdown().unwrap_or_default();
        let lines: Vec<&str> = content.lines().collect();
        let mut matches = Vec::new();

        for (idx, line) in lines.iter().enumerate() {
            if pattern.is_match(line) {
                // Collect context
                let context_before: Vec<String> = lines
                    [idx.saturating_sub(args.context)..idx]
                    .iter()
                    .map(|s| (*s).to_string())
                    .collect();

                let context_after: Vec<String> = lines
                    [(idx + 1).min(lines.len())..(idx + 1 + args.context).min(lines.len())]
                    .iter()
                    .map(|s| (*s).to_string())
                    .collect();

                matches.push(SearchMatch {
                    line_number: idx + 1,
                    line: (*line).to_string(),
                    context_before,
                    context_after,
                });

                total_matches += 1;
            }
        }

        if !matches.is_empty() {
            results.push((adr.clone(), matches));
        }

        // Check limit
        if let Some(limit) = args.limit {
            if results.len() >= limit {
                break;
            }
        }
    }

    if results.is_empty() {
        eprintln!("{} No matches found for: {}", "→".yellow(), args.query);
        return Ok(());
    }

    // Display results
    for (adr, matches) in &results {
        println!(
            "{} {} - {}",
            adr.id.cyan().bold(),
            format!("[{}]", adr.frontmatter.status).dimmed(),
            adr.frontmatter.title
        );

        for m in matches {
            // Print context before
            for ctx_line in &m.context_before {
                println!("  {} {}", "│".dimmed(), ctx_line.dimmed());
            }

            // Print matching line with highlighting
            let highlighted = pattern.replace_all(&m.line, |caps: &regex::Captures| {
                format!("{}", caps[0].red().bold())
            });
            println!(
                "  {} {}",
                format!("{}:", m.line_number).yellow(),
                highlighted
            );

            // Print context after
            for ctx_line in &m.context_after {
                println!("  {} {}", "│".dimmed(), ctx_line.dimmed());
            }

            println!();
        }
    }

    eprintln!(
        "{} {} match(es) in {} ADR(s)",
        "→".blue(),
        total_matches,
        results.len()
    );

    Ok(())
}
