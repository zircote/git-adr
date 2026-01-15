//! Initialize git-adr in a repository.

use anyhow::Result;
use clap::Args as ClapArgs;
use colored::Colorize;

use crate::core::{ConfigManager, Git};

/// Arguments for the init command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// Notes namespace (default: adr).
    #[arg(long, default_value = "adr")]
    pub namespace: String,

    /// Default ADR template format.
    #[arg(long, short, default_value = "madr")]
    pub template: String,

    /// ADR ID prefix.
    #[arg(long, default_value = "ADR-")]
    pub prefix: String,

    /// Number of digits in ADR ID.
    #[arg(long, default_value = "4")]
    pub digits: u8,

    /// Force reinitialization.
    #[arg(long, short)]
    pub force: bool,
}

/// Run the init command.
///
/// # Errors
///
/// Returns an error if initialization fails.
pub fn run(args: Args) -> Result<()> {
    let git = Git::new();

    // Verify we're in a git repository
    git.check_repository()?;

    let config_manager = ConfigManager::new(git.clone());

    // Check if already initialized
    if config_manager.is_initialized()? && !args.force {
        eprintln!(
            "{} git-adr is already initialized. Use --force to reinitialize.",
            "!".yellow()
        );
        return Ok(());
    }

    eprintln!("{} Initializing git-adr...", "→".blue());

    // Build configuration
    let config = crate::core::AdrConfig {
        prefix: args.prefix,
        digits: args.digits,
        template: args.template.clone(),
        format: args.template,
        initialized: true,
    };

    // Save configuration
    config_manager.save(&config)?;

    // Configure notes fetch/push refspecs for automatic sync
    let _ = git.config_set("remote.origin.fetch", "+refs/notes/*:refs/notes/*");

    eprintln!("  Prefix: {}", config.prefix);
    eprintln!("  Digits: {}", config.digits);
    eprintln!("  Template: {}", config.template);

    eprintln!("{} git-adr initialized successfully!", "✓".green());
    eprintln!();
    eprintln!("Next steps:");
    eprintln!("  git adr new \"Your First Decision\"");

    Ok(())
}
