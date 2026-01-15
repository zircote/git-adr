//! Show git log with ADR annotations.

use anyhow::Result;
use clap::Args as ClapArgs;

/// Arguments for the log command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// Number of commits to show.
    #[arg(short = 'n', default_value = "10")]
    pub count: usize,

    /// Show only commits with linked ADRs.
    #[arg(long)]
    pub linked_only: bool,
}

/// Run the log command.
///
/// # Errors
///
/// Returns an error if log fails.
pub fn run(args: Args) -> Result<()> {
    use colored::Colorize;

    eprintln!("{} Showing git log with ADR annotations", "→".blue());

    // TODO: Implement log logic
    // 1. Get recent commits
    // 2. Find linked ADRs
    // 3. Display annotated log

    let _ = args;

    Ok(())
}
