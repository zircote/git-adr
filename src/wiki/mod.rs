//! Wiki synchronization for git-adr.
//!
//! This module provides synchronization between ADRs and wiki platforms:
//! - GitHub Wiki
//! - GitLab Wiki

use crate::Error;

mod github;
mod gitlab;
mod service;

pub use service::{WikiConfig, WikiPlatform, WikiService};

/// Check if wiki features are available.
#[must_use]
pub fn is_available() -> bool {
    true
}

/// Detect the wiki platform from the git remote.
///
/// # Errors
///
/// Returns an error if detection fails.
pub fn detect_platform(remote_url: &str) -> Result<WikiPlatform, Error> {
    if remote_url.contains("github.com") {
        Ok(WikiPlatform::GitHub)
    } else if remote_url.contains("gitlab.com") || remote_url.contains("gitlab") {
        Ok(WikiPlatform::GitLab)
    } else {
        Err(Error::WikiError {
            message: format!("Unknown wiki platform for remote: {remote_url}"),
        })
    }
}
