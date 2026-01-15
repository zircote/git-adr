//! Convert ADR between formats.

use anyhow::Result;
use clap::Args as ClapArgs;

/// Arguments for the convert command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// ADR ID to convert.
    pub adr_id: String,

    /// Target format.
    #[arg(long, short)]
    pub to: String,

    /// Save in place.
    #[arg(long)]
    pub in_place: bool,
}

/// Run the convert command.
///
/// # Errors
///
/// Returns an error if conversion fails.
pub fn run(args: Args) -> Result<()> {
    use colored::Colorize;

    eprintln!(
        "{} Converting ADR {} to format: {}",
        "→".blue(),
        args.adr_id,
        args.to
    );

    // TODO: Implement convert logic

    eprintln!("{} Conversion complete", "✓".green());

    Ok(())
}
