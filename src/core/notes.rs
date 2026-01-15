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
    fn extract_id(&self, content: &str, commit: &str) -> Result<String, Error> {
        // Try to parse frontmatter and get ID field
        if let Some(id) = Self::extract_id_from_frontmatter(content) {
            return Ok(id);
        }

        // Fall back to generating from commit short hash
        let short = self.git.short_hash(commit)?;
        Ok(format!("{}{}", self.config.prefix, short))
    }

    /// Extract ID from YAML frontmatter if present.
    fn extract_id_from_frontmatter(content: &str) -> Option<String> {
        /// Helper struct for extracting just the ID from frontmatter.
        #[derive(serde::Deserialize)]
        struct FrontmatterId {
            id: Option<String>,
        }

        let content = content.trim();
        if !content.starts_with("---") {
            return None;
        }

        let rest = &content[3..];
        let end_marker = rest.find("\n---")?;
        let yaml_content = &rest[..end_marker];

        serde_yaml::from_str::<FrontmatterId>(yaml_content)
            .ok()
            .and_then(|fm| fm.id)
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
    use std::process::Command as StdCommand;
    use tempfile::TempDir;

    fn setup_git_repo() -> TempDir {
        let temp_dir = TempDir::new().expect("Failed to create temp directory");
        let path = temp_dir.path();

        StdCommand::new("git")
            .args(["init"])
            .current_dir(path)
            .output()
            .expect("Failed to init git repo");

        StdCommand::new("git")
            .args(["config", "user.email", "test@example.com"])
            .current_dir(path)
            .output()
            .expect("Failed to set git user email");

        StdCommand::new("git")
            .args(["config", "user.name", "Test User"])
            .current_dir(path)
            .output()
            .expect("Failed to set git user name");

        std::fs::write(path.join("README.md"), "# Test Repo\n").expect("Failed to write README");
        StdCommand::new("git")
            .args(["add", "."])
            .current_dir(path)
            .output()
            .expect("Failed to stage files");
        StdCommand::new("git")
            .args(["commit", "-m", "Initial commit"])
            .current_dir(path)
            .output()
            .expect("Failed to create initial commit");

        temp_dir
    }

    #[test]
    fn test_format_id() {
        let git = Git::new();
        let config = AdrConfig::default();
        let manager = NotesManager::new(git, config);

        assert_eq!(manager.format_id(1), "ADR-0001");
        assert_eq!(manager.format_id(42), "ADR-0042");
        assert_eq!(manager.format_id(9999), "ADR-9999");
    }

    #[test]
    fn test_format_id_custom_prefix() {
        let git = Git::new();
        let config = AdrConfig {
            prefix: "DECISION-".to_string(),
            digits: 3,
            ..Default::default()
        };
        let manager = NotesManager::new(git, config);

        assert_eq!(manager.format_id(1), "DECISION-001");
        assert_eq!(manager.format_id(99), "DECISION-099");
    }

    #[test]
    fn test_extract_id_from_frontmatter_with_id() {
        let content = r#"---
id: ADR-0001
title: Test
status: proposed
---

Body content
"#;
        let result = NotesManager::extract_id_from_frontmatter(content);
        assert_eq!(result, Some("ADR-0001".to_string()));
    }

    #[test]
    fn test_extract_id_from_frontmatter_without_id() {
        let content = r#"---
title: Test
status: proposed
---

Body content
"#;
        let result = NotesManager::extract_id_from_frontmatter(content);
        assert_eq!(result, None);
    }

    #[test]
    fn test_extract_id_from_frontmatter_no_frontmatter() {
        let content = "Just some plain text without frontmatter";
        let result = NotesManager::extract_id_from_frontmatter(content);
        assert_eq!(result, None);
    }

    #[test]
    fn test_extract_id_from_frontmatter_invalid_yaml() {
        let content = r#"---
invalid: yaml: content:
---
"#;
        let result = NotesManager::extract_id_from_frontmatter(content);
        assert_eq!(result, None);
    }

    #[test]
    fn test_notes_manager_git_accessor() {
        let git = Git::new();
        let config = AdrConfig::default();
        let manager = NotesManager::new(git, config);

        // Just verify we can access the git reference
        let _git_ref = manager.git();
    }

    #[test]
    fn test_notes_manager_config_accessor() {
        let git = Git::new();
        let config = AdrConfig {
            prefix: "TEST-".to_string(),
            ..Default::default()
        };
        let manager = NotesManager::new(git, config);

        assert_eq!(manager.config().prefix, "TEST-");
    }

    #[test]
    fn test_create_with_empty_commit() {
        let temp_dir = setup_git_repo();
        let git = Git::with_work_dir(temp_dir.path());
        let config = AdrConfig::default();
        let manager = NotesManager::new(git, config);

        // Create ADR with empty commit - should use HEAD
        let mut adr = Adr::new("ADR-0001".to_string(), "Test Decision".to_string());
        adr.commit = String::new(); // Empty commit

        let result = manager.create(&adr);
        assert!(result.is_ok());

        // Verify it was created
        let adrs = manager.list().expect("Should list ADRs");
        assert_eq!(adrs.len(), 1);
        assert_eq!(adrs[0].id, "ADR-0001");
    }

    #[test]
    fn test_get_by_commit() {
        let temp_dir = setup_git_repo();
        let git = Git::with_work_dir(temp_dir.path());
        let config = AdrConfig::default();
        let manager = NotesManager::new(git.clone(), config);

        // Get HEAD commit
        let head = git.head().expect("Should get HEAD");

        // Create ADR on this commit
        let adr = Adr::new("ADR-0001".to_string(), "Test Decision".to_string());
        manager.create(&adr).expect("Should create ADR");

        // Get by commit
        let retrieved = manager.get_by_commit(&head);
        assert!(retrieved.is_ok());
        let retrieved = retrieved.unwrap();
        assert_eq!(retrieved.id, "ADR-0001");
        assert_eq!(retrieved.frontmatter.title, "Test Decision");
    }

    #[test]
    fn test_get_by_commit_not_found() {
        let temp_dir = setup_git_repo();
        let git = Git::with_work_dir(temp_dir.path());
        let config = AdrConfig::default();
        let manager = NotesManager::new(git.clone(), config);

        // Get HEAD commit
        let head = git.head().expect("Should get HEAD");

        // Try to get by commit without creating an ADR
        let result = manager.get_by_commit(&head);
        assert!(result.is_err());
    }
}
