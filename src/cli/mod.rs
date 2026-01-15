//! CLI command definitions and handlers.
//!
//! This module defines the command-line interface using clap derive macros.

use clap::{Parser, Subcommand};

pub mod artifacts;
pub mod attach;
pub mod ci;
pub mod config;
pub mod convert;
pub mod edit;
pub mod export;
pub mod hooks;
pub mod import;
pub mod init;
pub mod link;
pub mod list;
pub mod log;
pub mod metrics;
pub mod new;
pub mod onboard;
pub mod report;
pub mod rm;
pub mod search;
pub mod show;
pub mod stats;
pub mod supersede;
pub mod sync;
pub mod templates;

#[cfg(feature = "ai")]
pub mod ai;

#[cfg(feature = "wiki")]
pub mod wiki;

/// Architecture Decision Records management using git notes.
///
/// git-adr stores ADRs in git notes, keeping your working tree clean while
/// maintaining full git history and sync capabilities.
#[derive(Parser, Debug)]
#[command(name = "git-adr")]
#[command(author, version, about, long_about = None)]
#[command(propagate_version = true)]
pub struct Cli {
    /// Subcommand to execute.
    #[command(subcommand)]
    pub command: Commands,
}

/// Available commands.
#[derive(Subcommand, Debug)]
pub enum Commands {
    /// Initialize git-adr in the repository.
    Init(init::Args),

    /// Create a new ADR.
    #[command(alias = "n")]
    New(new::Args),

    /// List all ADRs.
    #[command(alias = "l")]
    List(list::Args),

    /// Show an ADR.
    #[command(alias = "s")]
    Show(show::Args),

    /// Edit an existing ADR.
    #[command(alias = "e")]
    Edit(edit::Args),

    /// Remove an ADR.
    Rm(rm::Args),

    /// Search ADRs.
    Search(search::Args),

    /// Sync ADRs with remote.
    Sync(sync::Args),

    /// Manage configuration.
    Config(config::Args),

    /// Link ADR to commits.
    Link(link::Args),

    /// Create a superseding ADR.
    Supersede(supersede::Args),

    /// Show git log with ADR annotations.
    Log(log::Args),

    /// Show ADR statistics.
    Stats(stats::Args),

    /// Convert ADR between formats.
    Convert(convert::Args),

    /// Attach a file to an ADR.
    Attach(attach::Args),

    /// List artifacts attached to an ADR.
    Artifacts(artifacts::Args),

    /// Export ADRs to various formats.
    Export(export::Args),

    /// Import ADRs from files.
    Import(import::Args),

    /// Manage git hooks for ADR workflows.
    Hooks(hooks::Args),

    /// Generate CI/CD workflows for ADR integration.
    Ci(ci::Args),

    /// Generate project templates with ADR integration.
    Templates(templates::Args),

    /// Generate ADR analytics report.
    Report(report::Args),

    /// Export ADR metrics as JSON.
    Metrics(metrics::Args),

    /// Interactive onboarding wizard for new team members.
    Onboard(onboard::Args),

    /// AI-assisted ADR operations.
    #[cfg(feature = "ai")]
    Ai(ai::Args),

    /// Wiki synchronization.
    #[cfg(feature = "wiki")]
    Wiki(wiki::Args),
}
