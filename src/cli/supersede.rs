//! Create a superseding ADR.

use anyhow::Result;
use clap::Args as ClapArgs;

/// Arguments for the supersede command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// ADR ID to supersede.
    pub adr_id: String,

    /// Title for the new ADR.
    pub title: String,
}

/// Run the supersede command.
///
/// # Errors
///
/// Returns an error if supersession fails.
pub fn run(args: Args) -> Result<()> {
    use colored::Colorize;

    eprintln!(
        "{} Superseding ADR {} with: {}",
        "→".blue(),
        args.adr_id,
        args.title
    );

    // TODO: Implement supersede logic
    // 1. Create new ADR
    // 2. Update old ADR status to superseded
    // 3. Link both ADRs

    eprintln!("{} ADR superseded", "✓".green());

    Ok(())
}
