//! Sync ADRs with remote.

use anyhow::Result;
use clap::Args as ClapArgs;
use colored::Colorize;

use crate::core::{ConfigManager, Git, NotesManager};

/// Arguments for the sync command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// Remote name.
    #[arg(default_value = "origin")]
    pub remote: String,

    /// Pull only.
    #[arg(long)]
    pub pull: bool,

    /// Push only.
    #[arg(long)]
    pub push: bool,

    /// Force push (use with caution).
    #[arg(long, short)]
    pub force: bool,
}

/// Run the sync command.
///
/// # Errors
///
/// Returns an error if sync fails.
pub fn run(args: Args) -> Result<()> {
    let git = Git::new();
    git.check_repository()?;

    let config = ConfigManager::new(git.clone()).load()?;
    let notes = NotesManager::new(git, config);

    // Determine what operations to perform
    let do_push = args.push || !args.pull;
    let do_fetch = args.pull || !args.push;

    eprintln!(
        "{} Syncing with remote: {}",
        "→".blue(),
        args.remote.cyan()
    );

    if do_fetch {
        eprintln!("  Fetching notes...");
        match notes.sync(&args.remote, false, true) {
            Ok(()) => eprintln!("    {} Fetched ADR notes", "✓".green()),
            Err(e) => {
                // Fetch failures are often non-fatal (remote might not have notes yet)
                eprintln!(
                    "    {} Could not fetch notes: {}",
                    "!".yellow(),
                    e.to_string().lines().next().unwrap_or("unknown error")
                );
            }
        }
    }

    if do_push {
        eprintln!("  Pushing notes...");
        match notes.sync(&args.remote, true, false) {
            Ok(()) => eprintln!("    {} Pushed ADR notes", "✓".green()),
            Err(e) => {
                // Push failures are more serious
                eprintln!(
                    "    {} Failed to push notes: {}",
                    "✗".red(),
                    e.to_string().lines().next().unwrap_or("unknown error")
                );
                return Err(e.into());
            }
        }
    }

    eprintln!("{} Sync complete", "✓".green());

    Ok(())
}
