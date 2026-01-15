//! Show an ADR.

use anyhow::Result;
use clap::Args as ClapArgs;
use colored::Colorize;

use crate::core::{ConfigManager, Git, NotesManager};

/// Arguments for the show command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// ADR ID to show.
    pub adr_id: String,

    /// Output format (markdown, yaml, json).
    #[arg(long, short, default_value = "markdown")]
    pub format: String,

    /// Show only metadata.
    #[arg(long)]
    pub metadata_only: bool,
}

/// Run the show command.
///
/// # Errors
///
/// Returns an error if the ADR cannot be shown.
pub fn run(args: Args) -> Result<()> {
    let git = Git::new();
    git.check_repository()?;

    let config = ConfigManager::new(git.clone()).load()?;
    let notes = NotesManager::new(git, config);

    // Try to find ADR by ID (exact match or partial)
    let adrs = notes.list()?;
    let adr = adrs
        .into_iter()
        .find(|a| a.id == args.adr_id || a.id.contains(&args.adr_id))
        .ok_or_else(|| anyhow::anyhow!("ADR not found: {}", args.adr_id))?;

    match args.format.as_str() {
        "json" => {
            let output = if args.metadata_only {
                serde_json::json!({
                    "id": adr.id,
                    "title": adr.frontmatter.title,
                    "status": adr.frontmatter.status.to_string(),
                    "date": adr.frontmatter.date.as_ref().map(|d| d.datetime().to_rfc3339()),
                    "tags": adr.frontmatter.tags,
                    "authors": adr.frontmatter.authors,
                    "deciders": adr.frontmatter.deciders,
                    "commit": adr.commit,
                })
            } else {
                serde_json::json!({
                    "id": adr.id,
                    "title": adr.frontmatter.title,
                    "status": adr.frontmatter.status.to_string(),
                    "date": adr.frontmatter.date.as_ref().map(|d| d.datetime().to_rfc3339()),
                    "tags": adr.frontmatter.tags,
                    "authors": adr.frontmatter.authors,
                    "deciders": adr.frontmatter.deciders,
                    "commit": adr.commit,
                    "body": adr.body,
                })
            };
            println!("{}", serde_json::to_string_pretty(&output)?);
        },
        "yaml" => {
            if args.metadata_only {
                println!("{}", serde_yaml::to_string(&adr.frontmatter)?);
            } else {
                println!("{}", adr.to_markdown()?);
            }
        },
        _ => {
            if args.metadata_only {
                println!("{} {}", "ID:".bold(), adr.id.cyan());
                println!("{} {}", "Title:".bold(), adr.frontmatter.title);
                println!("{} {}", "Status:".bold(), adr.frontmatter.status);
                if let Some(date) = &adr.frontmatter.date {
                    println!("{} {}", "Date:".bold(), date.datetime().format("%Y-%m-%d"));
                }
                if !adr.frontmatter.tags.is_empty() {
                    println!("{} {}", "Tags:".bold(), adr.frontmatter.tags.join(", "));
                }
                println!("{} {}", "Commit:".bold(), &adr.commit[..8]);
            } else {
                println!("{}", adr.to_markdown()?);
            }
        },
    }

    Ok(())
}
