//! Link ADR to commits.

use anyhow::Result;
use clap::Args as ClapArgs;
use colored::Colorize;

use crate::core::{ConfigManager, Git, NotesManager};

/// Arguments for the link command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// ADR ID.
    pub adr_id: String,

    /// Commit SHA to link.
    pub commit: String,
}

/// Run the link command.
///
/// # Errors
///
/// Returns an error if linking fails.
pub fn run(args: Args) -> Result<()> {
    let git = Git::new();
    git.check_repository()?;

    let config = ConfigManager::new(git.clone()).load()?;
    let notes = NotesManager::new(git.clone(), config);

    // Find the ADR
    let adrs = notes.list()?;
    let adr = adrs
        .into_iter()
        .find(|a| a.id == args.adr_id || a.id.contains(&args.adr_id))
        .ok_or_else(|| anyhow::anyhow!("ADR not found: {}", args.adr_id))?;

    eprintln!(
        "{} Linking ADR {} to commit {}",
        "→".blue(),
        adr.id.cyan(),
        &args.commit[..8.min(args.commit.len())].yellow()
    );

    // Verify the target commit exists
    let full_commit = git.run_output(&["rev-parse", &args.commit])?;
    let full_commit = full_commit.trim().to_string();

    if adr.commit == full_commit {
        eprintln!("{} ADR is already linked to this commit", "!".yellow());
        return Ok(());
    }

    // Remove note from old commit
    notes.delete(&adr.id)?;

    // Create note on new commit
    let mut new_adr = adr.clone();
    new_adr.commit.clone_from(&full_commit);
    notes.create(&new_adr)?;

    eprintln!(
        "{} ADR {} moved from {} to {}",
        "✓".green(),
        adr.id,
        &adr.commit[..8],
        &full_commit[..8]
    );

    Ok(())
}
