//! Search ADRs.

use anyhow::Result;
use clap::Args as ClapArgs;

/// Arguments for the search command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// Search query.
    pub query: String,

    /// Filter by status.
    #[arg(long, short)]
    pub status: Option<String>,

    /// Filter by tag.
    #[arg(long, short = 'g')]
    pub tag: Option<String>,

    /// Case sensitive search.
    #[arg(long, short)]
    pub case_sensitive: bool,

    /// Use regex pattern.
    #[arg(long, short = 'E')]
    pub regex: bool,

    /// Context lines to show.
    #[arg(long, short = 'C', default_value = "2")]
    pub context: usize,

    /// Maximum results.
    #[arg(long)]
    pub limit: Option<usize>,
}

/// Run the search command.
///
/// # Errors
///
/// Returns an error if search fails.
pub fn run(args: Args) -> Result<()> {
    use colored::Colorize;

    eprintln!("{} Searching for: {}", "→".blue(), args.query);

    // TODO: Implement search logic
    // 1. Load index
    // 2. Search with filters
    // 3. Display results with highlighted matches

    eprintln!("{} No results found", "→".yellow());

    Ok(())
}
