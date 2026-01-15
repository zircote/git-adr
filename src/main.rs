//! git-adr CLI binary entry point.
//!
//! This is the main entry point for the `git-adr` command-line tool.

use anyhow::Result;
use clap::Parser;
use tracing_subscriber::EnvFilter;

use git_adr::cli::{Cli, Commands};

fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::fmt()
        .with_env_filter(
            EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("warn")),
        )
        .with_writer(std::io::stderr)
        .init();

    // Parse CLI arguments
    let cli = Cli::parse();

    // Execute command
    match cli.command {
        Commands::Init(args) => git_adr::cli::init::run(args),
        Commands::New(args) => git_adr::cli::new::run(args),
        Commands::List(args) => git_adr::cli::list::run(args),
        Commands::Show(args) => git_adr::cli::show::run(args),
        Commands::Edit(args) => git_adr::cli::edit::run(args),
        Commands::Rm(args) => git_adr::cli::rm::run(args),
        Commands::Search(args) => git_adr::cli::search::run(args),
        Commands::Sync(args) => git_adr::cli::sync::run(args),
        Commands::Config(args) => git_adr::cli::config::run(args),
        Commands::Link(args) => git_adr::cli::link::run(args),
        Commands::Supersede(args) => git_adr::cli::supersede::run(args),
        Commands::Log(args) => git_adr::cli::log::run(args),
        Commands::Stats(args) => git_adr::cli::stats::run(args),
        Commands::Convert(args) => git_adr::cli::convert::run(args),
        Commands::Attach(args) => git_adr::cli::attach::run(args),
        Commands::Artifacts(args) => git_adr::cli::artifacts::run(args),
        Commands::Export(args) => git_adr::cli::export::run(args),
        #[cfg(feature = "ai")]
        Commands::Ai(args) => git_adr::cli::ai::run(args),
        #[cfg(feature = "wiki")]
        Commands::Wiki(args) => git_adr::cli::wiki::run(args),
    }
}
