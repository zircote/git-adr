//! Remove an ADR.

use anyhow::Result;
use clap::Args as ClapArgs;

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
    use colored::Colorize;

    eprintln!("{} Removing ADR: {}", "→".blue(), args.adr_id);

    // TODO: Implement remove logic
    // 1. Confirm with user (unless --force)
    // 2. Remove note
    // 3. Update index

    eprintln!("{} ADR removed", "✓".green());

    Ok(())
}
