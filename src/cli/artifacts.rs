//! List artifacts attached to an ADR.

use anyhow::Result;
use clap::Args as ClapArgs;

/// Arguments for the artifacts command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// ADR ID.
    pub adr_id: String,
}

/// Run the artifacts command.
///
/// # Errors
///
/// Returns an error if listing fails.
pub fn run(args: Args) -> Result<()> {
    use colored::Colorize;

    eprintln!("{} Listing artifacts for ADR {}", "→".blue(), args.adr_id);

    // TODO: Implement artifacts listing logic

    eprintln!("{} No artifacts found", "→".yellow());

    Ok(())
}
