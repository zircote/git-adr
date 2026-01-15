//! Git notes management for ADRs.
//!
//! This module provides the `NotesManager` which handles CRUD operations
//! for ADRs stored in git notes.

use crate::core::{Adr, AdrConfig, Git};
use crate::Error;

/// Notes reference for ADR content.
pub const ADR_NOTES_REF: &str = "adr";
/// Notes reference for artifacts.
pub const ARTIFACTS_NOTES_REF: &str = "adr-artifacts";

/// Manager for ADR operations in git notes.
#[derive(Debug)]
pub struct NotesManager {
    git: Git,
    config: AdrConfig,
}

impl NotesManager {
    /// Create a new `NotesManager`.
    #[must_use]
    pub const fn new(git: Git, config: AdrConfig) -> Self {
        Self { git, config }
    }

    /// Get a reference to the Git wrapper.
    #[must_use]
    pub const fn git(&self) -> &Git {
        &self.git
    }

    /// Get a reference to the configuration.
    #[must_use]
    pub const fn config(&self) -> &AdrConfig {
        &self.config
    }

    /// List all ADRs.
    ///
    /// # Errors
    ///
    /// Returns an error if ADRs cannot be listed.
    pub fn list(&self) -> Result<Vec<Adr>, Error> {
        let notes = self.git.notes_list(ADR_NOTES_REF)?;
        let mut adrs = Vec::new();

        for (note_hash, commit) in notes {
            if let Some(content) = self.git.notes_show(ADR_NOTES_REF, &commit)? {
                // Extract ADR ID from the content or generate from commit
                let id = self.extract_id(&content, &commit)?;
                if let Ok(adr) = Adr::from_markdown(id, commit.clone(), &content) {
                    adrs.push(adr);
                }
            }
            let _ = note_hash; // Used for future artifact lookup
        }

        // Sort by ID
        adrs.sort_by(|a, b| a.id.cmp(&b.id));

        Ok(adrs)
    }

    /// Get an ADR by ID.
    ///
    /// # Errors
    ///
    /// Returns an error if the ADR is not found or cannot be read.
    pub fn get(&self, id: &str) -> Result<Adr, Error> {
        let adrs = self.list()?;
        adrs.into_iter()
            .find(|adr| adr.id == id)
            .ok_or_else(|| Error::AdrNotFound { id: id.to_string() })
    }

    /// Get an ADR by commit hash.
    ///
    /// # Errors
    ///
    /// Returns an error if the ADR is not found.
    pub fn get_by_commit(&self, commit: &str) -> Result<Adr, Error> {
        let content =
            self.git
                .notes_show(ADR_NOTES_REF, commit)?
                .ok_or_else(|| Error::AdrNotFound {
                    id: commit.to_string(),
                })?;

        let id = self.extract_id(&content, commit)?;
        Adr::from_markdown(id, commit.to_string(), &content)
    }

    /// Create a new ADR.
    ///
    /// # Errors
    ///
    /// Returns an error if the ADR cannot be created.
    pub fn create(&self, adr: &Adr) -> Result<(), Error> {
        let commit = if adr.commit.is_empty() {
            self.git.head()?
        } else {
            adr.commit.clone()
        };

        let content = adr.to_markdown()?;
        self.git.notes_add(ADR_NOTES_REF, &commit, &content)?;

        Ok(())
    }

    /// Update an existing ADR.
    ///
    /// # Errors
    ///
    /// Returns an error if the ADR cannot be updated.
    pub fn update(&self, adr: &Adr) -> Result<(), Error> {
        // Verify ADR exists
        let _ = self.get(&adr.id)?;

        let content = adr.to_markdown()?;
        self.git.notes_add(ADR_NOTES_REF, &adr.commit, &content)?;

        Ok(())
    }

    /// Delete an ADR.
    ///
    /// # Errors
    ///
    /// Returns an error if the ADR cannot be deleted.
    pub fn delete(&self, id: &str) -> Result<(), Error> {
        let adr = self.get(id)?;
        self.git.notes_remove(ADR_NOTES_REF, &adr.commit)?;
        Ok(())
    }

    /// Get the next available ADR number.
    ///
    /// # Errors
    ///
    /// Returns an error if ADRs cannot be listed.
    pub fn next_number(&self) -> Result<u32, Error> {
        let adrs = self.list()?;
        let max_num = adrs
            .iter()
            .filter_map(|adr| {
                adr.id
                    .strip_prefix(&self.config.prefix)
                    .and_then(|s| s.parse::<u32>().ok())
            })
            .max()
            .unwrap_or(0);

        Ok(max_num + 1)
    }

    /// Generate an ADR ID for the given number.
    #[must_use]
    pub fn format_id(&self, number: u32) -> String {
        format!(
            "{}{:0width$}",
            self.config.prefix,
            number,
            width = self.config.digits as usize
        )
    }

    /// Extract ADR ID from content or generate from commit.
    fn extract_id(&self, _content: &str, commit: &str) -> Result<String, Error> {
        // TODO: Try to find ID in frontmatter or content
        // For now, generate from commit short hash
        let short = self.git.short_hash(commit)?;
        Ok(format!("{}{}", self.config.prefix, short))
    }

    /// Sync notes with remote.
    ///
    /// # Errors
    ///
    /// Returns an error if sync fails.
    pub fn sync(&self, remote: &str, push: bool, fetch: bool) -> Result<(), Error> {
        if fetch {
            // Fetch notes (ignore errors if ref doesn't exist on remote)
            let _ = self.git.notes_fetch(remote, ADR_NOTES_REF);
            let _ = self.git.notes_fetch(remote, ARTIFACTS_NOTES_REF);
        }

        if push {
            self.git.notes_push(remote, ADR_NOTES_REF)?;
            // Only push artifacts if they exist
            let _ = self.git.notes_push(remote, ARTIFACTS_NOTES_REF);
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::AdrConfig;

    #[test]
    fn test_format_id() {
        let git = Git::new();
        let config = AdrConfig::default();
        let manager = NotesManager::new(git, config);

        assert_eq!(manager.format_id(1), "ADR-0001");
        assert_eq!(manager.format_id(42), "ADR-0042");
        assert_eq!(manager.format_id(9999), "ADR-9999");
    }
}
