//! Wiki service abstraction.

use crate::core::Adr;
use crate::wiki::{github::GitHubWiki, gitlab::GitLabWiki};
use crate::Error;

/// Supported wiki platforms.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum WikiPlatform {
    /// GitHub Wiki.
    GitHub,
    /// GitLab Wiki.
    GitLab,
}

impl std::fmt::Display for WikiPlatform {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::GitHub => write!(f, "github"),
            Self::GitLab => write!(f, "gitlab"),
        }
    }
}

/// Configuration for wiki synchronization.
#[derive(Debug, Clone)]
pub struct WikiConfig {
    /// The platform to use.
    pub platform: WikiPlatform,
    /// Repository identifier (owner/repo for GitHub, project path for GitLab).
    pub repository: String,
    /// API token for authentication.
    pub token: Option<String>,
    /// Base URL for self-hosted instances.
    pub base_url: Option<String>,
}

impl WikiConfig {
    /// Create a new wiki configuration.
    #[must_use]
    pub fn new(platform: WikiPlatform, repository: impl Into<String>) -> Self {
        Self {
            platform,
            repository: repository.into(),
            token: None,
            base_url: None,
        }
    }

    /// Set the API token.
    #[must_use]
    pub fn with_token(mut self, token: impl Into<String>) -> Self {
        self.token = Some(token.into());
        self
    }

    /// Set the base URL.
    #[must_use]
    pub fn with_base_url(mut self, url: impl Into<String>) -> Self {
        self.base_url = Some(url.into());
        self
    }
}

/// Wiki service for synchronizing ADRs.
#[derive(Debug)]
pub struct WikiService {
    config: WikiConfig,
}

impl WikiService {
    /// Create a new wiki service.
    #[must_use]
    pub fn new(config: WikiConfig) -> Self {
        Self { config }
    }

    /// Push an ADR to the wiki.
    ///
    /// # Errors
    ///
    /// Returns an error if the push fails.
    pub fn push(&self, adr: &Adr) -> Result<(), Error> {
        match self.config.platform {
            WikiPlatform::GitHub => {
                let parts: Vec<&str> = self.config.repository.split('/').collect();
                if parts.len() != 2 {
                    return Err(Error::WikiError {
                        message: format!(
                            "Invalid GitHub repository format: {}",
                            self.config.repository
                        ),
                    });
                }
                let wiki = GitHubWiki::new(parts[0], parts[1]);
                wiki.push(adr)
            },
            WikiPlatform::GitLab => {
                let wiki = GitLabWiki::new(&self.config.repository);
                wiki.push(adr)
            },
        }
    }

    /// Pull an ADR from the wiki.
    ///
    /// # Errors
    ///
    /// Returns an error if the pull fails.
    pub fn pull(&self, id: &str) -> Result<Adr, Error> {
        match self.config.platform {
            WikiPlatform::GitHub => {
                let parts: Vec<&str> = self.config.repository.split('/').collect();
                if parts.len() != 2 {
                    return Err(Error::WikiError {
                        message: format!(
                            "Invalid GitHub repository format: {}",
                            self.config.repository
                        ),
                    });
                }
                let wiki = GitHubWiki::new(parts[0], parts[1]);
                wiki.pull(id)
            },
            WikiPlatform::GitLab => {
                let wiki = GitLabWiki::new(&self.config.repository);
                wiki.pull(id)
            },
        }
    }

    /// Sync all ADRs with the wiki.
    ///
    /// # Errors
    ///
    /// Returns an error if sync fails.
    pub fn sync(&self, adrs: &[Adr]) -> Result<SyncResult, Error> {
        let mut result = SyncResult::default();

        for adr in adrs {
            match self.push(adr) {
                Ok(()) => result.pushed += 1,
                Err(e) => {
                    result.errors.push(format!("{}: {e}", adr.id));
                },
            }
        }

        Ok(result)
    }
}

/// Result of a wiki sync operation.
#[derive(Debug, Default)]
pub struct SyncResult {
    /// Number of ADRs pushed.
    pub pushed: usize,
    /// Number of ADRs pulled.
    pub pulled: usize,
    /// Errors encountered.
    pub errors: Vec<String>,
}
