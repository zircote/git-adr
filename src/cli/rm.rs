//! Remove an ADR.

use anyhow::Result;
use clap::Args as ClapArgs;
use colored::Colorize;
use std::io::{self, Write};

use crate::core::{ConfigManager, Git, NotesManager};

/// Arguments for the rm command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// ADR ID to remove.
    pub adr_id: String,

    /// Skip confirmation prompt.
    #[arg(long, short)]
    pub force: bool,
}

/// Run the rm command.
///
/// # Errors
///
/// Returns an error if removal fails.
pub fn run(args: Args) -> Result<()> {
    let git = Git::new();
    git.check_repository()?;

    let config = ConfigManager::new(git.clone()).load()?;
    let notes = NotesManager::new(git, config);

    // Find the ADR to confirm it exists
    let adrs = notes.list()?;
    let adr = adrs
        .into_iter()
        .find(|a| a.id == args.adr_id || a.id.contains(&args.adr_id))
        .ok_or_else(|| anyhow::anyhow!("ADR not found: {}", args.adr_id))?;

    eprintln!("{} ADR: {} - {}", "→".blue(), adr.id, adr.frontmatter.title);
    eprintln!("  Status: {}", adr.frontmatter.status);

    // Confirm deletion unless --force
    if !args.force {
        eprint!("Are you sure you want to remove this ADR? [y/N] ");
        io::stderr().flush()?;

        let mut input = String::new();
        io::stdin().read_line(&mut input)?;

        if !input.trim().eq_ignore_ascii_case("y") {
            eprintln!("{} Aborted", "!".yellow());
            return Ok(());
        }
    }

    // Delete the ADR
    notes.delete(&adr.id)?;

    eprintln!("{} ADR removed: {}", "✓".green(), adr.id);

    Ok(())
}
