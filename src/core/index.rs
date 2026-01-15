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
        // Use the first commit in the repository
        let output = self
            .git
            .run_output(&["rev-list", "--max-parents=0", "HEAD"])?;
        let first_line = output.lines().next().unwrap_or("").trim();

        if first_line.is_empty() {
            // No commits yet, use HEAD
            self.git.head()
        } else {
            Ok(first_line.to_string())
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
}
