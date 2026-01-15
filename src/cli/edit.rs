//! Edit an existing ADR.

use anyhow::Result;
use clap::Args as ClapArgs;
use colored::Colorize;

use crate::core::{AdrStatus, ConfigManager, Git, NotesManager};

/// Arguments for the edit command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// ADR ID to edit.
    pub adr_id: String,

    /// Quick edit: change status.
    #[arg(long, short)]
    pub status: Option<String>,

    /// Quick edit: add tag.
    #[arg(long)]
    pub add_tag: Option<String>,

    /// Quick edit: remove tag.
    #[arg(long)]
    pub remove_tag: Option<String>,

    /// Quick edit: change title.
    #[arg(long, short)]
    pub title: Option<String>,

    /// Quick edit: add decider.
    #[arg(long)]
    pub add_decider: Option<String>,

    /// Quick edit: remove decider.
    #[arg(long)]
    pub remove_decider: Option<String>,
}

/// Run the edit command.
///
/// # Errors
///
/// Returns an error if editing fails.
#[allow(clippy::useless_let_if_seq)]
pub fn run(args: Args) -> Result<()> {
    let git = Git::new();
    git.check_repository()?;

    let config = ConfigManager::new(git.clone()).load()?;
    let notes = NotesManager::new(git, config);

    // Find the ADR
    let adrs = notes.list()?;
    let mut adr = adrs
        .into_iter()
        .find(|a| a.id == args.adr_id || a.id.contains(&args.adr_id))
        .ok_or_else(|| anyhow::anyhow!("ADR not found: {}", args.adr_id))?;

    eprintln!("{} Editing ADR: {}", "→".blue(), adr.id);

    let mut modified = false;

    // Apply quick edits
    if let Some(status_str) = &args.status {
        let status: AdrStatus = status_str.parse().map_err(|e| anyhow::anyhow!("{}", e))?;
        eprintln!("  Status: {} → {}", adr.frontmatter.status, status);
        adr.frontmatter.status = status;
        modified = true;
    }

    if let Some(title) = &args.title {
        eprintln!("  Title: {} → {}", adr.frontmatter.title, title);
        adr.frontmatter.title.clone_from(title);
        modified = true;
    }

    if let Some(tag) = &args.add_tag {
        if adr.frontmatter.tags.contains(tag) {
            eprintln!("  Tag already exists: {}", tag);
        } else {
            adr.frontmatter.tags.push(tag.clone());
            eprintln!("  Added tag: {}", tag);
            modified = true;
        }
    }

    if let Some(tag) = &args.remove_tag {
        if let Some(pos) = adr.frontmatter.tags.iter().position(|t| t == tag) {
            adr.frontmatter.tags.remove(pos);
            eprintln!("  Removed tag: {}", tag);
            modified = true;
        } else {
            eprintln!("  Tag not found: {}", tag);
        }
    }

    if let Some(decider) = &args.add_decider {
        if adr.frontmatter.deciders.contains(decider) {
            eprintln!("  Decider already exists: {}", decider);
        } else {
            adr.frontmatter.deciders.push(decider.clone());
            eprintln!("  Added decider: {}", decider);
            modified = true;
        }
    }

    if let Some(decider) = &args.remove_decider {
        if let Some(pos) = adr.frontmatter.deciders.iter().position(|d| d == decider) {
            adr.frontmatter.deciders.remove(pos);
            eprintln!("  Removed decider: {}", decider);
            modified = true;
        } else {
            eprintln!("  Decider not found: {}", decider);
        }
    }

    if !modified {
        eprintln!("{} No changes specified", "!".yellow());
        return Ok(());
    }

    // Save changes
    notes.update(&adr)?;

    eprintln!("{} ADR updated: {}", "✓".green(), adr.id);

    Ok(())
}
