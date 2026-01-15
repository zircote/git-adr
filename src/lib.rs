//! git-adr: Architecture Decision Records management using git notes
//!
//! This crate provides a library and CLI tool for managing Architecture Decision Records (ADRs)
//! stored in git notes. ADRs are stored in `refs/notes/adr` and can be synchronized across
//! remotes like regular git content.
//!
//! # Features
//!
//! - Store ADRs in git notes (non-intrusive, no file clutter)
//! - Multiple ADR formats (MADR, Nygard, Y-Statement, Alexandrian, etc.)
//! - Full-text search and indexing
//! - Binary artifact attachments
//! - Sync with remotes
//! - Optional AI integration for drafting and suggestions
//! - Optional wiki sync (GitHub, GitLab)
//! - Export to multiple formats (Markdown, JSON, HTML, DOCX)
//!
//! # Example
//!
//! ```no_run
//! use git_adr::core::{Git, NotesManager, ConfigManager};
//!
//! // Initialize git executor
//! let git = Git::new();
//!
//! // Load configuration
//! let config = ConfigManager::new(git.clone()).load()?;
//!
//! // Create notes manager
//! let notes = NotesManager::new(git, config);
//!
//! // List all ADRs
//! let adrs = notes.list()?;
//! for adr in adrs {
//!     println!("{}: {}", adr.id, adr.title());
//! }
//! # Ok::<(), git_adr::Error>(())
//! ```

// Lints are configured in Cargo.toml [lints] section
#![allow(clippy::struct_excessive_bools)]
#![allow(clippy::needless_pass_by_value)]

pub mod cli;
pub mod core;

#[cfg(feature = "ai")]
pub mod ai;

#[cfg(feature = "wiki")]
pub mod wiki;

#[cfg(feature = "export")]
pub mod export;

use thiserror::Error;

/// Result type alias for git-adr operations.
pub type Result<T> = std::result::Result<T, Error>;

/// Errors that can occur in git-adr operations.
#[derive(Error, Debug)]
pub enum Error {
    /// Git command execution failed.
    #[error("git error: {message}")]
    Git {
        /// Error message.
        message: String,
        /// Git command that failed.
        command: Vec<String>,
        /// Exit code from git.
        exit_code: i32,
        /// Standard error output.
        stderr: String,
    },

    /// Git executable not found.
    #[error("git executable not found - please install git")]
    GitNotFound,

    /// Not in a git repository.
    #[error("not a git repository{}", path.as_ref().map(|p| format!(": {p}")).unwrap_or_default())]
    NotARepository {
        /// Path that was checked.
        path: Option<String>,
    },

    /// git-adr not initialized in this repository.
    #[error("git-adr not initialized - run 'git adr init' first")]
    NotInitialized,

    /// ADR not found.
    #[error("ADR not found: {id}")]
    AdrNotFound {
        /// ADR ID that was not found.
        id: String,
    },

    /// Invalid ADR format.
    #[error("invalid ADR format: {message}")]
    InvalidAdr {
        /// Error message.
        message: String,
    },

    /// YAML parsing error.
    #[error("YAML error: {0}")]
    Yaml(#[from] serde_yaml::Error),

    /// JSON parsing error.
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),

    /// IO error.
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    /// Template rendering error.
    #[error("template error: {0}")]
    Template(#[from] tera::Error),

    /// Configuration error.
    #[error("configuration error: {message}")]
    Config {
        /// Error message.
        message: String,
    },

    /// Validation error.
    #[error("validation error: {message}")]
    Validation {
        /// Error message.
        message: String,
    },

    /// Content too large.
    #[error("content too large: {size} bytes (max: {max} bytes)")]
    ContentTooLarge {
        /// Actual size.
        size: usize,
        /// Maximum allowed size.
        max: usize,
    },

    /// Feature not available.
    #[error("feature not available: {feature} - install with 'cargo install git-adr --features {feature}'")]
    FeatureNotAvailable {
        /// Feature name.
        feature: String,
    },

    /// Invalid status value.
    #[error("invalid status '{status}', valid values are: {}", valid.join(", "))]
    InvalidStatus {
        /// The invalid status provided.
        status: String,
        /// Valid status values.
        valid: Vec<String>,
    },

    /// Parse error.
    #[error("parse error: {message}")]
    ParseError {
        /// Error message.
        message: String,
    },

    /// Template error.
    #[error("template error: {message}")]
    TemplateError {
        /// Error message.
        message: String,
    },

    /// Template not found.
    #[error("template not found: {name}")]
    TemplateNotFound {
        /// Template name.
        name: String,
    },

    /// AI not configured.
    #[cfg(feature = "ai")]
    #[error("AI not configured: {message}")]
    AiNotConfigured {
        /// Error message.
        message: String,
    },

    /// Invalid AI provider.
    #[cfg(feature = "ai")]
    #[error("invalid AI provider: {provider}")]
    InvalidProvider {
        /// Provider name.
        provider: String,
    },

    /// Wiki error.
    #[cfg(feature = "wiki")]
    #[error("wiki error: {message}")]
    WikiError {
        /// Error message.
        message: String,
    },

    /// Export error.
    #[cfg(feature = "export")]
    #[error("export error: {message}")]
    ExportError {
        /// Error message.
        message: String,
    },

    /// Invalid format.
    #[error("invalid format: {format}")]
    InvalidFormat {
        /// Format name.
        format: String,
    },

    /// IO error with context.
    #[error("IO error: {message}")]
    IoError {
        /// Error message.
        message: String,
    },

    /// Generic error with message.
    #[error("{0}")]
    Other(String),
}

impl Error {
    /// Create a git error.
    #[must_use]
    pub fn git(
        message: impl Into<String>,
        command: Vec<String>,
        exit_code: i32,
        stderr: impl Into<String>,
    ) -> Self {
        Self::Git {
            message: message.into(),
            command,
            exit_code,
            stderr: stderr.into(),
        }
    }

    /// Create an ADR not found error.
    #[must_use]
    pub fn adr_not_found(id: impl Into<String>) -> Self {
        Self::AdrNotFound { id: id.into() }
    }

    /// Create an invalid ADR error.
    #[must_use]
    pub fn invalid_adr(message: impl Into<String>) -> Self {
        Self::InvalidAdr {
            message: message.into(),
        }
    }

    /// Create a config error.
    #[must_use]
    pub fn config(message: impl Into<String>) -> Self {
        Self::Config {
            message: message.into(),
        }
    }

    /// Create a validation error.
    #[must_use]
    pub fn validation(message: impl Into<String>) -> Self {
        Self::Validation {
            message: message.into(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_git() {
        let err = Error::git(
            "command failed",
            vec!["git".to_string(), "status".to_string()],
            1,
            "error output",
        );
        assert!(matches!(err, Error::Git { .. }));
        assert!(format!("{err}").contains("git error"));
    }

    #[test]
    fn test_error_adr_not_found() {
        let err = Error::adr_not_found("ADR-0001");
        assert!(format!("{err}").contains("ADR not found"));
    }

    #[test]
    fn test_error_invalid_adr() {
        let err = Error::invalid_adr("invalid content");
        assert!(format!("{err}").contains("invalid ADR format"));
    }

    #[test]
    fn test_error_config() {
        let err = Error::config("config error");
        assert!(format!("{err}").contains("configuration error"));
    }

    #[test]
    fn test_error_validation() {
        let err = Error::validation("validation failed");
        assert!(format!("{err}").contains("validation error"));
    }

    #[test]
    fn test_error_not_initialized() {
        let err = Error::NotInitialized;
        assert!(format!("{err}").contains("not initialized"));
    }

    #[test]
    fn test_error_git_not_found() {
        let err = Error::GitNotFound;
        assert!(format!("{err}").contains("git executable not found"));
    }

    #[test]
    fn test_error_not_a_repository() {
        let err = Error::NotARepository { path: Some("/tmp/test".to_string()) };
        assert!(format!("{err}").contains("not a git repository"));
        assert!(format!("{err}").contains("/tmp/test"));
    }

    #[test]
    fn test_error_not_a_repository_no_path() {
        let err = Error::NotARepository { path: None };
        let msg = format!("{err}");
        assert!(msg.contains("not a git repository"));
    }

    #[test]
    fn test_error_content_too_large() {
        let err = Error::ContentTooLarge { size: 1024, max: 512 };
        assert!(format!("{err}").contains("content too large"));
    }

    #[test]
    fn test_error_feature_not_available() {
        let err = Error::FeatureNotAvailable { feature: "ai".to_string() };
        assert!(format!("{err}").contains("feature not available"));
    }

    #[test]
    fn test_error_invalid_status() {
        let err = Error::InvalidStatus {
            status: "invalid".to_string(),
            valid: vec!["proposed".to_string(), "accepted".to_string()],
        };
        assert!(format!("{err}").contains("invalid status"));
    }

    #[test]
    fn test_error_parse_error() {
        let err = Error::ParseError { message: "parse failed".to_string() };
        assert!(format!("{err}").contains("parse error"));
    }

    #[test]
    fn test_error_template_not_found() {
        let err = Error::TemplateNotFound { name: "custom".to_string() };
        assert!(format!("{err}").contains("template not found"));
    }

    #[test]
    fn test_error_other() {
        let err = Error::Other("generic error".to_string());
        assert!(format!("{err}").contains("generic error"));
    }
}
