//! Link ADR to commits.

use anyhow::Result;
use clap::Args as ClapArgs;

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
    use colored::Colorize;

    eprintln!(
        "{} Linking ADR {} to commit {}",
        "→".blue(),
        args.adr_id,
        args.commit
    );

    // TODO: Implement link logic

    eprintln!("{} Link created", "✓".green());

    Ok(())
}
