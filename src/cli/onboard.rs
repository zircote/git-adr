//! Interactive onboarding wizard for new team members.

use anyhow::Result;
use clap::Args as ClapArgs;
use colored::Colorize;
use std::collections::HashMap;
use std::io::{self, Write};

use crate::core::{AdrStatus, ConfigManager, Git, NotesManager};

/// Arguments for the onboard command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// Show only accepted ADRs.
    #[arg(long)]
    pub accepted_only: bool,

    /// Show ADRs by category/tag.
    #[arg(long)]
    pub by_tag: bool,

    /// Skip interactive prompts.
    #[arg(long)]
    pub non_interactive: bool,

    /// Limit number of ADRs to show.
    #[arg(long, short, default_value = "10")]
    pub limit: usize,
}

/// Run the onboard command.
///
/// # Errors
///
/// Returns an error if onboarding fails.
pub fn run(args: Args) -> Result<()> {
    let git = Git::new();
    git.check_repository()?;

    let config = ConfigManager::new(git.clone()).load()?;
    let notes = NotesManager::new(git, config);

    let adrs = notes.list()?;

    if adrs.is_empty() {
        println!();
        println!("{}", "Welcome to Architecture Decision Records!".bold().cyan());
        println!();
        println!("This repository doesn't have any ADRs yet.");
        println!();
        println!("Get started by creating your first ADR:");
        println!("  {} git adr new \"Use git-adr for architecture decisions\"", "→".blue());
        println!();
        return Ok(());
    }

    // Filter ADRs if needed
    let filtered_adrs: Vec<_> = if args.accepted_only {
        adrs.iter()
            .filter(|a| matches!(a.frontmatter.status, AdrStatus::Accepted))
            .collect()
    } else {
        adrs.iter().collect()
    };

    println!();
    println!("{}", "═══════════════════════════════════════════".dimmed());
    println!("{}", "  Architecture Decision Records - Onboarding".bold().cyan());
    println!("{}", "═══════════════════════════════════════════".dimmed());
    println!();

    // Summary
    print_summary(&adrs);

    if args.by_tag {
        show_by_tag(&filtered_adrs, &args)?;
    } else {
        show_overview(&filtered_adrs, &args)?;
    }

    // Interactive mode
    if !args.non_interactive {
        interactive_browse(&filtered_adrs, &notes)?;
    }

    println!();
    println!("{}", "Quick Reference:".bold());
    println!("  {} List all ADRs          ", "git adr list".cyan());
    println!("  {} View specific ADR      ", "git adr show <id>".cyan());
    println!("  {} Search ADRs            ", "git adr search <query>".cyan());
    println!("  {} Create new ADR         ", "git adr new <title>".cyan());
    println!();

    Ok(())
}

/// Print summary statistics.
fn print_summary(adrs: &[crate::core::Adr]) {
    let mut status_counts: HashMap<&AdrStatus, usize> = HashMap::new();
    for adr in adrs {
        *status_counts.entry(&adr.frontmatter.status).or_insert(0) += 1;
    }

    println!("{}", "Summary".bold());
    println!("  Total ADRs: {}", adrs.len().to_string().cyan());

    let accepted = status_counts.get(&AdrStatus::Accepted).unwrap_or(&0);
    let proposed = status_counts.get(&AdrStatus::Proposed).unwrap_or(&0);
    let deprecated = status_counts.get(&AdrStatus::Deprecated).unwrap_or(&0);
    let superseded = status_counts.get(&AdrStatus::Superseded).unwrap_or(&0);

    println!(
        "  {} accepted, {} proposed, {} deprecated/superseded",
        accepted.to_string().green(),
        proposed.to_string().yellow(),
        (deprecated + superseded).to_string().dimmed()
    );
    println!();
}

/// Show ADR overview.
fn show_overview(adrs: &[&crate::core::Adr], args: &Args) -> Result<()> {
    println!("{}", "Key Decisions".bold());
    println!();

    let display_count = args.limit.min(adrs.len());

    for adr in adrs.iter().take(display_count) {
        let status_color = match adr.frontmatter.status {
            AdrStatus::Accepted => "accepted".green(),
            AdrStatus::Proposed => "proposed".yellow(),
            AdrStatus::Deprecated => "deprecated".dimmed(),
            AdrStatus::Superseded => "superseded".dimmed(),
            AdrStatus::Rejected => "rejected".red(),
        };

        println!(
            "  {} {} [{}]",
            adr.id.cyan(),
            adr.frontmatter.title,
            status_color
        );

        // Show tags if present
        if !adr.frontmatter.tags.is_empty() {
            let tags: Vec<&str> = adr.frontmatter.tags.iter().take(3).map(String::as_str).collect();
            println!("       Tags: {}", tags.join(", ").dimmed());
        }
    }

    if adrs.len() > display_count {
        println!();
        println!(
            "  {} ... and {} more (use --limit to show more)",
            "→".dimmed(),
            (adrs.len() - display_count).to_string().dimmed()
        );
    }

    println!();
    Ok(())
}

/// Show ADRs organized by tag.
fn show_by_tag(adrs: &[&crate::core::Adr], _args: &Args) -> Result<()> {
    // Collect ADRs by tag
    let mut by_tag: HashMap<String, Vec<&crate::core::Adr>> = HashMap::new();

    for adr in adrs {
        if adr.frontmatter.tags.is_empty() {
            by_tag.entry("uncategorized".to_string()).or_default().push(adr);
        } else {
            for tag in &adr.frontmatter.tags {
                by_tag.entry(tag.clone()).or_default().push(adr);
            }
        }
    }

    // Sort tags by count
    let mut tags: Vec<_> = by_tag.iter().collect();
    tags.sort_by(|a, b| b.1.len().cmp(&a.1.len()));

    println!("{}", "Decisions by Category".bold());
    println!();

    for (tag, tag_adrs) in tags.iter().take(10) {
        println!("  {} ({} ADRs)", tag.bold().cyan(), tag_adrs.len());

        for adr in tag_adrs.iter().take(3) {
            let status = match adr.frontmatter.status {
                AdrStatus::Accepted => "✓".green(),
                AdrStatus::Proposed => "○".yellow(),
                _ => "·".dimmed(),
            };
            println!("    {} {} {}", status, adr.id.dimmed(), adr.frontmatter.title);
        }

        if tag_adrs.len() > 3 {
            println!("    {} ... {} more", "→".dimmed(), tag_adrs.len() - 3);
        }
        println!();
    }

    Ok(())
}

/// Interactive browse mode.
fn interactive_browse(adrs: &[&crate::core::Adr], notes: &NotesManager) -> Result<()> {
    println!("{}", "Interactive Browse".bold());
    println!("  Enter an ADR ID to view details, or press Enter to skip.");
    println!();

    loop {
        print!("  {} ", "ADR ID (or 'q' to quit):".dimmed());
        io::stdout().flush()?;

        let mut input = String::new();
        io::stdin().read_line(&mut input)?;
        let input = input.trim();

        if input.is_empty() || input.eq_ignore_ascii_case("q") {
            break;
        }

        // Find matching ADR
        let matching = adrs.iter().find(|a| {
            a.id.eq_ignore_ascii_case(input) || a.id.contains(input)
        });

        match matching {
            Some(adr) => {
                println!();
                println!("{}", "─".repeat(50).dimmed());
                println!("{} {}", adr.id.bold().cyan(), adr.frontmatter.title.bold());
                println!("{}", "─".repeat(50).dimmed());
                println!();
                println!("{}: {}", "Status".bold(), adr.frontmatter.status);

                if let Some(date) = &adr.frontmatter.date {
                    println!("{}: {}", "Date".bold(), date.0.format("%Y-%m-%d"));
                }

                if !adr.frontmatter.tags.is_empty() {
                    println!("{}: {}", "Tags".bold(), adr.frontmatter.tags.join(", "));
                }

                // Show body preview
                let body_preview: String = adr.body.chars().take(500).collect();
                if !body_preview.is_empty() {
                    println!();
                    println!("{}", body_preview);
                    if adr.body.len() > 500 {
                        println!("{}...", "".dimmed());
                    }
                }

                println!();
                println!(
                    "  {} View full: git adr show {}",
                    "→".blue(),
                    adr.id.cyan()
                );
                println!();
            }
            None => {
                // Try to get from notes manager directly
                if let Ok(adr) = notes.get(input) {
                    println!();
                    println!("{}: {}", adr.id.cyan(), adr.frontmatter.title);
                    println!("Status: {}", adr.frontmatter.status);
                    println!();
                } else {
                    println!("  {} ADR not found: {}", "!".yellow(), input);
                }
            }
        }
    }

    Ok(())
}
