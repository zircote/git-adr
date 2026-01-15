//! Manage configuration.

use anyhow::Result;
use clap::{Args as ClapArgs, Subcommand};

/// Arguments for the config command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// Config subcommand.
    #[command(subcommand)]
    pub command: ConfigCommand,
}

/// Config subcommands.
#[derive(Subcommand, Debug)]
pub enum ConfigCommand {
    /// Get a configuration value.
    Get {
        /// Configuration key.
        key: String,
    },
    /// Set a configuration value.
    Set {
        /// Configuration key.
        key: String,
        /// Configuration value.
        value: String,
    },
    /// Unset a configuration value.
    Unset {
        /// Configuration key.
        key: String,
    },
    /// List all configuration values.
    List,
}

/// Run the config command.
///
/// # Errors
///
/// Returns an error if config operation fails.
pub fn run(args: Args) -> Result<()> {
    use colored::Colorize;

    match args.command {
        ConfigCommand::Get { key } => {
            eprintln!("{} Getting config: {}", "→".blue(), key);
            // TODO: Implement get
        },
        ConfigCommand::Set { key, value } => {
            eprintln!("{} Setting config: {} = {}", "→".blue(), key, value);
            // TODO: Implement set
        },
        ConfigCommand::Unset { key } => {
            eprintln!("{} Unsetting config: {}", "→".blue(), key);
            // TODO: Implement unset
        },
        ConfigCommand::List => {
            eprintln!("{} Listing config", "→".blue());
            // TODO: Implement list
        },
    }

    Ok(())
}
