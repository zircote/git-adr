//! GitLab Wiki integration.

use crate::core::Adr;
use crate::Error;

/// GitLab Wiki client.
#[derive(Debug)]
#[allow(dead_code)] // Fields used via API methods (stub implementation)
pub struct GitLabWiki {
    /// Project ID or path.
    pub project: String,
    /// GitLab API token.
    pub token: Option<String>,
    /// GitLab API base URL.
    pub base_url: String,
}

impl GitLabWiki {
    /// Create a new GitLab Wiki client.
    #[must_use]
    pub fn new(project: impl Into<String>) -> Self {
        Self {
            project: project.into(),
            token: std::env::var("GITLAB_TOKEN").ok(),
            base_url: std::env::var("GITLAB_URL")
                .unwrap_or_else(|_| "https://gitlab.com".to_string()),
        }
    }

    /// Push an ADR to the wiki.
    ///
    /// # Errors
    ///
    /// Returns an error if the push fails.
    pub fn push(&self, adr: &Adr) -> Result<(), Error> {
        // TODO: Implement GitLab Wiki API push
        let _ = adr;
        Err(Error::WikiError {
            message: "GitLab Wiki push not yet implemented".to_string(),
        })
    }

    /// Pull an ADR from the wiki.
    ///
    /// # Errors
    ///
    /// Returns an error if the pull fails.
    pub fn pull(&self, id: &str) -> Result<Adr, Error> {
        // TODO: Implement GitLab Wiki API pull
        Err(Error::WikiError {
            message: format!("GitLab Wiki pull not yet implemented for {id}"),
        })
    }

    /// List all ADRs in the wiki.
    ///
    /// # Errors
    ///
    /// Returns an error if listing fails.
    #[allow(dead_code)] // Will be used when wiki feature is fully implemented
    pub fn list(&self) -> Result<Vec<String>, Error> {
        // TODO: Implement GitLab Wiki API listing
        Err(Error::WikiError {
            message: "GitLab Wiki listing not yet implemented".to_string(),
        })
    }
}
