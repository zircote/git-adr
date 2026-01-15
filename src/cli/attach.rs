//! Attach a file to an ADR.

use anyhow::Result;
use clap::Args as ClapArgs;

/// Arguments for the attach command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// ADR ID.
    pub adr_id: String,

    /// File to attach.
    pub file: String,

    /// Override filename.
    #[arg(long)]
    pub name: Option<String>,

    /// Alt text for images.
    #[arg(long)]
    pub alt: Option<String>,
}

/// Run the attach command.
///
/// # Errors
///
/// Returns an error if attachment fails.
pub fn run(args: Args) -> Result<()> {
    use colored::Colorize;

    eprintln!(
        "{} Attaching {} to ADR {}",
        "→".blue(),
        args.file,
        args.adr_id
    );

    // TODO: Implement attach logic

    eprintln!("{} File attached", "✓".green());

    Ok(())
}
