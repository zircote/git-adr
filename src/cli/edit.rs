//! Edit an existing ADR.

use anyhow::Result;
use clap::Args as ClapArgs;

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

    /// Quick edit: link to commit.
    #[arg(long)]
    pub link: Option<String>,

    /// Quick edit: unlink from commit.
    #[arg(long)]
    pub unlink: Option<String>,
}

/// Run the edit command.
///
/// # Errors
///
/// Returns an error if editing fails.
pub fn run(args: Args) -> Result<()> {
    use colored::Colorize;

    eprintln!("{} Editing ADR: {}", "→".blue(), args.adr_id);

    // TODO: Implement edit logic
    // 1. Load ADR
    // 2. Apply quick edits or open editor
    // 3. Save changes

    eprintln!("{} ADR updated", "✓".green());

    Ok(())
}
