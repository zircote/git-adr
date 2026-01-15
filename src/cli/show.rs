//! Show an ADR.

use anyhow::Result;
use clap::Args as ClapArgs;

/// Arguments for the show command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// ADR ID to show.
    pub adr_id: String,

    /// Output format (markdown, yaml, json).
    #[arg(long, short, default_value = "markdown")]
    pub format: String,

    /// Show only metadata.
    #[arg(long)]
    pub metadata_only: bool,

    /// Disable interactive mode.
    #[arg(long)]
    pub no_interactive: bool,
}

/// Run the show command.
///
/// # Errors
///
/// Returns an error if the ADR cannot be shown.
pub fn run(args: Args) -> Result<()> {
    use colored::Colorize;

    eprintln!("{} Showing ADR: {}", "→".blue(), args.adr_id);

    // TODO: Implement show logic
    // 1. Load notes manager
    // 2. Get ADR by ID
    // 3. Format and display

    eprintln!("{} ADR not found: {}", "✗".red(), args.adr_id);

    Ok(())
}
