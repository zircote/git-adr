//! Show git log with ADR annotations.

use anyhow::Result;
use clap::Args as ClapArgs;
use colored::Colorize;

use crate::core::{ConfigManager, Git, NotesManager};

/// Arguments for the log command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// Number of commits to show.
    #[arg(short = 'n', default_value = "10")]
    pub count: usize,

    /// Show only commits with linked ADRs.
    #[arg(long)]
    pub linked_only: bool,

    /// Commit range or ref (default: HEAD).
    #[arg(default_value = "HEAD")]
    pub revision: String,
}

/// Run the log command.
///
/// # Errors
///
/// Returns an error if log fails.
pub fn run(args: Args) -> Result<()> {
    let git = Git::new();
    git.check_repository()?;

    let config = ConfigManager::new(git.clone()).load()?;
    let notes = NotesManager::new(git.clone(), config);

    // Get ADRs indexed by commit
    let adrs = notes.list()?;
    let adr_map: std::collections::HashMap<String, Vec<_>> =
        adrs.into_iter().fold(std::collections::HashMap::new(), |mut acc, adr| {
            acc.entry(adr.commit.clone()).or_default().push(adr);
            acc
        });

    // Get recent commits
    let log_output = git.run_output(&[
        "log",
        "--format=%H|%h|%s|%an|%ar",
        &format!("-{}", args.count),
        &args.revision,
    ])?;

    let mut displayed = 0;

    for line in log_output.lines() {
        let parts: Vec<&str> = line.splitn(5, '|').collect();
        if parts.len() < 5 {
            continue;
        }

        let (full_hash, short_hash, subject, author, date) =
            (parts[0], parts[1], parts[2], parts[3], parts[4]);

        let linked_adrs = adr_map.get(full_hash);

        // Skip if --linked-only and no ADRs
        if args.linked_only && linked_adrs.is_none() {
            continue;
        }

        // Print commit info
        println!(
            "{} {} - {} ({}, {})",
            short_hash.yellow(),
            subject,
            author.dimmed(),
            date.dimmed(),
            if linked_adrs.is_some() {
                "📋".to_string()
            } else {
                "  ".to_string()
            }
        );

        // Print linked ADRs
        if let Some(adrs) = linked_adrs {
            for adr in adrs {
                println!(
                    "  {} {} [{}] - {}",
                    "└─".dimmed(),
                    adr.id.cyan().bold(),
                    adr.frontmatter.status.to_string().dimmed(),
                    adr.frontmatter.title
                );
            }
        }

        displayed += 1;
    }

    if displayed == 0 {
        eprintln!("{} No commits found", "!".yellow());
    } else {
        eprintln!();
        eprintln!(
            "{} {} commit(s) shown, {} with ADRs",
            "→".blue(),
            displayed,
            adr_map.len()
        );
    }

    Ok(())
}
