//! GitHub Wiki integration.

use crate::core::Adr;
use crate::Error;

/// GitHub Wiki client.
#[derive(Debug)]
#[allow(dead_code)] // Fields used via API methods (stub implementation)
pub struct GitHubWiki {
    /// Repository owner.
    pub owner: String,
    /// Repository name.
    pub repo: String,
    /// GitHub API token.
    pub token: Option<String>,
}

impl GitHubWiki {
    /// Create a new GitHub Wiki client.
    #[must_use]
    pub fn new(owner: impl Into<String>, repo: impl Into<String>) -> Self {
        Self {
            owner: owner.into(),
            repo: repo.into(),
            token: std::env::var("GITHUB_TOKEN").ok(),
        }
    }

    /// Push an ADR to the wiki.
    ///
    /// # Errors
    ///
    /// Returns an error if the push fails.
    pub fn push(&self, adr: &Adr) -> Result<(), Error> {
        // TODO: Implement GitHub Wiki push via git clone/push
        let _ = adr;
        Err(Error::WikiError {
            message: "GitHub Wiki push not yet implemented".to_string(),
        })
    }

    /// Pull an ADR from the wiki.
    ///
    /// # Errors
    ///
    /// Returns an error if the pull fails.
    pub fn pull(&self, id: &str) -> Result<Adr, Error> {
        // TODO: Implement GitHub Wiki pull
        Err(Error::WikiError {
            message: format!("GitHub Wiki pull not yet implemented for {id}"),
        })
    }

    /// List all ADRs in the wiki.
    ///
    /// # Errors
    ///
    /// Returns an error if listing fails.
    #[allow(dead_code)] // Will be used when wiki feature is fully implemented
    pub fn list(&self) -> Result<Vec<String>, Error> {
        // TODO: Implement GitHub Wiki listing
        Err(Error::WikiError {
            message: "GitHub Wiki listing not yet implemented".to_string(),
        })
    }
}
