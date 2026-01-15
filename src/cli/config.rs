//! Manage configuration.

use anyhow::Result;
use clap::{Args as ClapArgs, Subcommand};
use colored::Colorize;

use crate::core::{ConfigManager, Git};

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

/// Known configuration keys with descriptions.
const CONFIG_KEYS: &[(&str, &str)] = &[
    ("initialized", "Whether git-adr is initialized (true/false)"),
    ("prefix", "Prefix for ADR IDs (default: ADR-)"),
    ("digits", "Number of digits in ADR IDs (default: 4)"),
    ("template", "Default template name"),
    ("format", "Default ADR format (nygard, madr, etc.)"),
];

/// Run the config command.
///
/// # Errors
///
/// Returns an error if config operation fails.
pub fn run(args: Args) -> Result<()> {
    let git = Git::new();
    git.check_repository()?;

    let config_manager = ConfigManager::new(git.clone());

    match args.command {
        ConfigCommand::Get { key } => {
            if let Some(v) = config_manager.get(&key)? {
                println!("{}", v);
            } else {
                eprintln!("{} Config key not set: adr.{}", "!".yellow(), key);
                std::process::exit(1);
            }
        }
        ConfigCommand::Set { key, value } => {
            // Validate known keys
            if !CONFIG_KEYS.iter().any(|(k, _)| *k == key) {
                eprintln!(
                    "{} Unknown config key: {}. Known keys are:",
                    "!".yellow(),
                    key
                );
                for (k, desc) in CONFIG_KEYS {
                    eprintln!("  {} - {}", k.cyan(), desc);
                }
                eprintln!();
                eprintln!("Setting anyway...");
            }

            config_manager.set(&key, &value)?;
            eprintln!(
                "{} Set adr.{} = {}",
                "✓".green(),
                key.cyan(),
                value.yellow()
            );
        }
        ConfigCommand::Unset { key } => {
            // Use git directly to unset the key
            git.config_unset(&format!("adr.{key}"), false)?;
            eprintln!("{} Unset adr.{}", "✓".green(), key.cyan());
        }
        ConfigCommand::List => {
            eprintln!("{} ADR Configuration:", "→".blue());
            eprintln!();

            let config = config_manager.load()?;

            println!("{} = {}", "adr.initialized".cyan(), config.initialized);
            println!("{} = {}", "adr.prefix".cyan(), config.prefix);
            println!("{} = {}", "adr.digits".cyan(), config.digits);
            println!("{} = {}", "adr.template".cyan(), config.template);
            println!("{} = {}", "adr.format".cyan(), config.format);
        }
    }

    Ok(())
}
