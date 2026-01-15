//! Create a new ADR.

use anyhow::Result;
use clap::Args as ClapArgs;

/// Arguments for the new command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// ADR title.
    pub title: String,

    /// Initial status.
    #[arg(long, short, default_value = "proposed")]
    pub status: String,

    /// Tags (can be specified multiple times).
    #[arg(long, short = 'g')]
    pub tag: Vec<String>,

    /// Deciders (can be specified multiple times).
    #[arg(long, short)]
    pub deciders: Vec<String>,

    /// Link to commit SHA.
    #[arg(long, short)]
    pub link: Option<String>,

    /// Template format to use.
    #[arg(long)]
    pub template: Option<String>,

    /// Read content from file.
    #[arg(long, short)]
    pub file: Option<String>,

    /// Don't open editor.
    #[arg(long)]
    pub no_edit: bool,

    /// Preview without saving.
    #[arg(long)]
    pub preview: bool,

    /// Create as draft.
    #[arg(long)]
    pub draft: bool,
}

/// Run the new command.
///
/// # Errors
///
/// Returns an error if ADR creation fails.
pub fn run(args: Args) -> Result<()> {
    use colored::Colorize;

    eprintln!("{} Creating new ADR: {}", "→".blue(), args.title);

    // TODO: Implement ADR creation logic
    // 1. Generate ADR ID
    // 2. Render template
    // 3. Open editor (unless --no-edit)
    // 4. Parse frontmatter
    // 5. Store in git notes

    let adr_id = format!(
        "{}-{}",
        chrono::Local::now().format("%Y%m%d"),
        args.title.to_lowercase().replace(' ', "-")
    );

    eprintln!("{} Created ADR: {}", "✓".green(), adr_id);

    Ok(())
}
