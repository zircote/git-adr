//! Show ADR statistics.

use anyhow::Result;
use clap::Args as ClapArgs;

/// Arguments for the stats command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// Output format (text, json).
    #[arg(long, short, default_value = "text")]
    pub format: String,
}

/// Run the stats command.
///
/// # Errors
///
/// Returns an error if stats fails.
pub fn run(args: Args) -> Result<()> {
    use colored::Colorize;

    eprintln!("{} ADR Statistics", "→".blue());

    // TODO: Implement stats logic
    // 1. Load index
    // 2. Calculate statistics
    // 3. Display

    let _ = args;

    Ok(())
}
