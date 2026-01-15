//! List all ADRs.

use anyhow::Result;
use clap::Args as ClapArgs;

/// Arguments for the list command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// Filter by status.
    #[arg(long, short)]
    pub status: Option<String>,

    /// Filter by tag.
    #[arg(long, short = 'g')]
    pub tag: Option<String>,

    /// Filter by date (since).
    #[arg(long)]
    pub since: Option<String>,

    /// Filter by date (until).
    #[arg(long)]
    pub until: Option<String>,

    /// Output format (table, json, csv, oneline).
    #[arg(long, short, default_value = "table")]
    pub format: String,

    /// Reverse sort order.
    #[arg(long, short)]
    pub reverse: bool,
}

/// Run the list command.
///
/// # Errors
///
/// Returns an error if listing fails.
pub fn run(args: Args) -> Result<()> {
    use colored::Colorize;

    // TODO: Implement list logic
    // 1. Load notes manager
    // 2. Query index with filters
    // 3. Format and display results

    eprintln!(
        "{} No ADRs found. Create one with: git adr new \"Title\"",
        "→".yellow()
    );

    let _ = args; // Suppress unused warning for now

    Ok(())
}
