//! Core functionality for git-adr.
//!
//! This module contains the core abstractions for managing ADRs:
//! - [`Adr`] - The ADR data model
//! - [`Git`] - Low-level git operations
//! - [`NotesManager`] - CRUD operations for ADRs in git notes
//! - [`IndexManager`] - Search index operations
//! - [`ConfigManager`] - Configuration management
//! - [`TemplateEngine`] - Template rendering

mod adr;
mod config;
mod git;
mod index;
mod notes;
mod templates;

pub use adr::{Adr, AdrStatus};
pub use config::{AdrConfig, ConfigManager};
pub use git::Git;
pub use index::IndexManager;
pub use notes::NotesManager;
pub use templates::TemplateEngine;
