//! Search index for ADRs.
//!
//! This module provides full-text search capabilities for ADRs
//! using an index stored in git notes.

use crate::core::{Adr, Git, NotesManager};
use crate::Error;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Notes reference for the search index.
pub const INDEX_NOTES_REF: &str = "adr-index";

/// A search index entry for an ADR.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IndexEntry {
    /// ADR ID.
    pub id: String,
    /// Commit hash.
    pub commit: String,
    /// ADR title.
    pub title: String,
    /// ADR status.
    pub status: String,
    /// Tags.
    pub tags: Vec<String>,
    /// Full-text content for searching.
    pub text: String,
}

impl IndexEntry {
    /// Create an index entry from an ADR.
    #[must_use]
    pub fn from_adr(adr: &Adr) -> Self {
        Self {
            id: adr.id.clone(),
            commit: adr.commit.clone(),
            title: adr.frontmatter.title.clone(),
            status: adr.frontmatter.status.to_string(),
            tags: adr.frontmatter.tags.clone(),
            text: format!(
                "{} {} {}",
                adr.frontmatter.title,
                adr.frontmatter.tags.join(" "),
                adr.body
            )
            .to_lowercase(),
        }
    }

    /// Check if this entry matches a query.
    #[must_use]
    pub fn matches(&self, query: &str) -> bool {
        let query_lower = query.to_lowercase();
        self.text.contains(&query_lower)
            || self.id.to_lowercase().contains(&query_lower)
            || self.title.to_lowercase().contains(&query_lower)
    }
}

/// The search index.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct SearchIndex {
    /// Index entries by ADR ID.
    pub entries: HashMap<String, IndexEntry>,
    /// Version of the index format.
    pub version: u32,
}

impl SearchIndex {
    /// Create a new empty index.
    #[must_use]
    pub fn new() -> Self {
        Self {
            entries: HashMap::new(),
            version: 1,
        }
    }

    /// Add or update an entry.
    pub fn upsert(&mut self, entry: IndexEntry) {
        self.entries.insert(entry.id.clone(), entry);
    }

    /// Remove an entry.
    pub fn remove(&mut self, id: &str) {
        self.entries.remove(id);
    }

    /// Search the index.
    #[must_use]
    pub fn search(&self, query: &str) -> Vec<&IndexEntry> {
        self.entries
            .values()
            .filter(|entry| entry.matches(query))
            .collect()
    }

    /// Get all entries.
    #[must_use]
    pub fn all(&self) -> Vec<&IndexEntry> {
        self.entries.values().collect()
    }
}

/// Manager for the search index.
#[derive(Debug)]
pub struct IndexManager {
    git: Git,
}

impl IndexManager {
    /// Create a new `IndexManager`.
    #[must_use]
    pub const fn new(git: Git) -> Self {
        Self { git }
    }

    /// Load the index from git notes.
    ///
    /// # Errors
    ///
    /// Returns an error if the index cannot be loaded.
    pub fn load(&self) -> Result<SearchIndex, Error> {
        // We store the index in a note attached to a special "index" ref
        // For simplicity, we use the repo's initial commit or a fixed hash
        let commit = self.get_index_commit()?;

        match self.git.notes_show(INDEX_NOTES_REF, &commit)? {
            Some(content) => serde_yaml::from_str(&content).map_err(|e| Error::ParseError {
                message: format!("Failed to parse index: {e}"),
            }),
            None => Ok(SearchIndex::new()),
        }
    }

    /// Save the index to git notes.
    ///
    /// # Errors
    ///
    /// Returns an error if the index cannot be saved.
    pub fn save(&self, index: &SearchIndex) -> Result<(), Error> {
        let commit = self.get_index_commit()?;
        let content = serde_yaml::to_string(index).map_err(|e| Error::ParseError {
            message: format!("Failed to serialize index: {e}"),
        })?;

        self.git.notes_add(INDEX_NOTES_REF, &commit, &content)?;

        Ok(())
    }

    /// Rebuild the index from all ADRs.
    ///
    /// # Errors
    ///
    /// Returns an error if the index cannot be rebuilt.
    pub fn rebuild(&self, notes: &NotesManager) -> Result<SearchIndex, Error> {
        let adrs = notes.list()?;
        let mut index = SearchIndex::new();

        for adr in &adrs {
            index.upsert(IndexEntry::from_adr(adr));
        }

        self.save(&index)?;

        Ok(index)
    }

    /// Search for ADRs matching a query.
    ///
    /// # Errors
    ///
    /// Returns an error if the search fails.
    pub fn search(&self, query: &str) -> Result<Vec<IndexEntry>, Error> {
        let index = self.load()?;
        Ok(index.search(query).into_iter().cloned().collect())
    }

    /// Get the commit hash used to store the index.
    fn get_index_commit(&self) -> Result<String, Error> {
        // Try to get the first commit in the repository
        // This may fail in empty repositories with no commits
        match self
            .git
            .run_output(&["rev-list", "--max-parents=0", "HEAD"])
        {
            Ok(output) => {
                let first_line = output.lines().next().unwrap_or("").trim();
                if first_line.is_empty() {
                    // No commits yet, use HEAD (may also fail)
                    self.git.head()
                } else {
                    Ok(first_line.to_string())
                }
            },
            Err(_) => {
                // Empty repository with no commits - try HEAD, then fall back to empty tree
                self.git.head().or_else(|_| {
                    // Use git's empty tree hash as fallback for truly empty repos
                    Ok("4b825dc642cb6eb9a060e54bf8d69288fbee4904".to_string())
                })
            },
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_index_entry_matches() {
        let entry = IndexEntry {
            id: "ADR-0001".to_string(),
            commit: "abc123".to_string(),
            title: "Use Rust for CLI".to_string(),
            status: "proposed".to_string(),
            tags: vec!["architecture".to_string()],
            text: "use rust for cli architecture".to_string(),
        };

        assert!(entry.matches("rust"));
        assert!(entry.matches("RUST"));
        assert!(entry.matches("adr-0001"));
        assert!(!entry.matches("python"));
    }

    #[test]
    fn test_index_entry_from_adr() {
        let mut adr = Adr::new("ADR-0001".to_string(), "Test Title".to_string());
        adr.commit = "abc123".to_string();
        adr.frontmatter.tags = vec!["rust".to_string(), "cli".to_string()];
        adr.body = "This is the body content.".to_string();

        let entry = IndexEntry::from_adr(&adr);
        assert_eq!(entry.id, "ADR-0001");
        assert_eq!(entry.commit, "abc123");
        assert_eq!(entry.title, "Test Title");
        assert_eq!(entry.status, "proposed");
        assert_eq!(entry.tags, vec!["rust", "cli"]);
        assert!(entry.text.contains("test title"));
        assert!(entry.text.contains("this is the body content"));
    }

    #[test]
    fn test_search_index() {
        let mut index = SearchIndex::new();
        index.upsert(IndexEntry {
            id: "ADR-0001".to_string(),
            commit: "abc123".to_string(),
            title: "Use Rust".to_string(),
            status: "proposed".to_string(),
            tags: vec![],
            text: "use rust".to_string(),
        });
        index.upsert(IndexEntry {
            id: "ADR-0002".to_string(),
            commit: "def456".to_string(),
            title: "Use Python".to_string(),
            status: "accepted".to_string(),
            tags: vec![],
            text: "use python".to_string(),
        });

        assert_eq!(index.search("rust").len(), 1);
        assert_eq!(index.search("use").len(), 2);
        assert_eq!(index.search("java").len(), 0);
    }

    #[test]
    fn test_search_index_remove() {
        let mut index = SearchIndex::new();
        index.upsert(IndexEntry {
            id: "ADR-0001".to_string(),
            commit: "abc123".to_string(),
            title: "Use Rust".to_string(),
            status: "proposed".to_string(),
            tags: vec![],
            text: "use rust".to_string(),
        });

        assert_eq!(index.entries.len(), 1);
        index.remove("ADR-0001");
        assert_eq!(index.entries.len(), 0);
    }

    #[test]
    fn test_search_index_all() {
        let mut index = SearchIndex::new();
        index.upsert(IndexEntry {
            id: "ADR-0001".to_string(),
            commit: "abc123".to_string(),
            title: "First".to_string(),
            status: "proposed".to_string(),
            tags: vec![],
            text: "first".to_string(),
        });
        index.upsert(IndexEntry {
            id: "ADR-0002".to_string(),
            commit: "def456".to_string(),
            title: "Second".to_string(),
            status: "accepted".to_string(),
            tags: vec![],
            text: "second".to_string(),
        });

        let all = index.all();
        assert_eq!(all.len(), 2);
    }

    #[test]
    fn test_search_index_upsert_updates() {
        let mut index = SearchIndex::new();
        index.upsert(IndexEntry {
            id: "ADR-0001".to_string(),
            commit: "abc123".to_string(),
            title: "Original".to_string(),
            status: "proposed".to_string(),
            tags: vec![],
            text: "original".to_string(),
        });

        index.upsert(IndexEntry {
            id: "ADR-0001".to_string(),
            commit: "abc123".to_string(),
            title: "Updated".to_string(),
            status: "accepted".to_string(),
            tags: vec![],
            text: "updated".to_string(),
        });

        assert_eq!(index.entries.len(), 1);
        assert_eq!(index.entries.get("ADR-0001").unwrap().title, "Updated");
    }

    #[test]
    fn test_search_index_new() {
        let index = SearchIndex::new();
        assert_eq!(index.version, 1);
        assert!(index.entries.is_empty());
    }

    #[test]
    fn test_search_index_default() {
        let index = SearchIndex::default();
        assert_eq!(index.version, 0); // Default doesn't set version to 1
        assert!(index.entries.is_empty());
    }

    #[test]
    fn test_index_entry_matches_by_id() {
        let entry = IndexEntry {
            id: "ADR-0001".to_string(),
            commit: "abc123".to_string(),
            title: "Something Else".to_string(),
            status: "proposed".to_string(),
            tags: vec![],
            text: "something else".to_string(),
        };
        // Should match by ID
        assert!(entry.matches("ADR-0001"));
        assert!(entry.matches("adr-0001"));
    }

    #[test]
    fn test_index_entry_matches_by_title() {
        let entry = IndexEntry {
            id: "ADR-0001".to_string(),
            commit: "abc123".to_string(),
            title: "Use PostgreSQL for Database".to_string(),
            status: "proposed".to_string(),
            tags: vec![],
            text: "some text".to_string(),
        };
        // Should match by title
        assert!(entry.matches("PostgreSQL"));
        assert!(entry.matches("POSTGRESQL"));
    }

    #[test]
    fn test_index_manager_new() {
        let git = Git::new();
        let _manager = IndexManager::new(git);
        // Just verify it creates without panic
    }

    #[test]
    fn test_search_index_clone() {
        let mut index = SearchIndex::new();
        index.upsert(IndexEntry {
            id: "ADR-0001".to_string(),
            commit: "abc123".to_string(),
            title: "Test".to_string(),
            status: "proposed".to_string(),
            tags: vec!["test".to_string()],
            text: "test".to_string(),
        });
        let cloned = index.clone();
        assert_eq!(cloned.entries.len(), 1);
        assert_eq!(cloned.version, index.version);
    }

    #[test]
    fn test_index_entry_clone() {
        let entry = IndexEntry {
            id: "ADR-0001".to_string(),
            commit: "abc123".to_string(),
            title: "Test".to_string(),
            status: "proposed".to_string(),
            tags: vec!["test".to_string()],
            text: "test content".to_string(),
        };
        let cloned = entry.clone();
        assert_eq!(cloned.id, entry.id);
        assert_eq!(cloned.commit, entry.commit);
        assert_eq!(cloned.title, entry.title);
        assert_eq!(cloned.tags, entry.tags);
    }

    #[test]
    fn test_search_index_serialization() {
        let mut index = SearchIndex::new();
        index.upsert(IndexEntry {
            id: "ADR-0001".to_string(),
            commit: "abc123".to_string(),
            title: "Test".to_string(),
            status: "proposed".to_string(),
            tags: vec!["tag1".to_string()],
            text: "test".to_string(),
        });

        let yaml = serde_yaml::to_string(&index).expect("Should serialize");
        let deserialized: SearchIndex = serde_yaml::from_str(&yaml).expect("Should deserialize");
        assert_eq!(deserialized.version, index.version);
        assert_eq!(deserialized.entries.len(), index.entries.len());
    }

    use crate::core::{AdrConfig, NotesManager};
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
    fn test_index_manager_load_empty() {
        let temp_dir = setup_git_repo();
        let git = Git::with_work_dir(temp_dir.path());
        let manager = IndexManager::new(git);

        // Load should return empty index when none exists
        let index = manager.load().expect("Should load");
        assert!(index.entries.is_empty());
    }

    #[test]
    fn test_index_manager_save_and_load() {
        let temp_dir = setup_git_repo();
        let git = Git::with_work_dir(temp_dir.path());
        let manager = IndexManager::new(git);

        // Create and save an index
        let mut index = SearchIndex::new();
        index.upsert(IndexEntry {
            id: "ADR-0001".to_string(),
            commit: "abc123".to_string(),
            title: "Test".to_string(),
            status: "proposed".to_string(),
            tags: vec!["tag1".to_string()],
            text: "test".to_string(),
        });

        manager.save(&index).expect("Should save");

        // Load it back
        let loaded = manager.load().expect("Should load");
        assert_eq!(loaded.entries.len(), 1);
        assert!(loaded.entries.contains_key("ADR-0001"));
    }

    #[test]
    fn test_index_manager_rebuild() {
        let temp_dir = setup_git_repo();
        let git = Git::with_work_dir(temp_dir.path());
        let config = AdrConfig::default();
        let notes = NotesManager::new(git.clone(), config);
        let index_manager = IndexManager::new(git);

        // Create an ADR
        let adr = Adr::new("ADR-0001".to_string(), "Test Decision".to_string());
        notes.create(&adr).expect("Should create ADR");

        // Rebuild index
        let index = index_manager.rebuild(&notes).expect("Should rebuild");
        assert_eq!(index.entries.len(), 1);
        assert!(index.entries.contains_key("ADR-0001"));
    }

    #[test]
    fn test_index_manager_search() {
        let temp_dir = setup_git_repo();
        let git = Git::with_work_dir(temp_dir.path());
        let config = AdrConfig::default();
        let notes = NotesManager::new(git.clone(), config);
        let index_manager = IndexManager::new(git);

        // Create ADRs
        let adr1 = Adr::new("ADR-0001".to_string(), "Use Rust for CLI".to_string());
        notes.create(&adr1).expect("Should create ADR");

        // Create another commit for second ADR
        std::fs::write(temp_dir.path().join("file1.txt"), "content").expect("Failed to write");
        StdCommand::new("git")
            .args(["add", "."])
            .current_dir(temp_dir.path())
            .output()
            .expect("Failed to stage");
        StdCommand::new("git")
            .args(["commit", "-m", "Second commit"])
            .current_dir(temp_dir.path())
            .output()
            .expect("Failed to commit");

        let adr2 = Adr::new("ADR-0002".to_string(), "Use Python for Scripts".to_string());
        notes.create(&adr2).expect("Should create ADR");

        // Rebuild index
        index_manager.rebuild(&notes).expect("Should rebuild");

        // Search
        let results = index_manager.search("Rust").expect("Should search");
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].id, "ADR-0001");

        // Search for both
        let results = index_manager.search("Use").expect("Should search");
        assert_eq!(results.len(), 2);
    }

    #[test]
    fn test_index_manager_get_index_commit() {
        let temp_dir = setup_git_repo();
        let git = Git::with_work_dir(temp_dir.path());
        let manager = IndexManager::new(git);

        // get_index_commit is private, but we can test it indirectly via save/load
        let mut index = SearchIndex::new();
        manager.save(&index).expect("Should save");
        index = manager.load().expect("Should load");
        assert_eq!(index.version, 1);
    }
}
