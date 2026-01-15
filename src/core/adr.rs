//! ADR data model.
//!
//! This module defines the core ADR structure that represents an
//! Architecture Decision Record with its metadata and content.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Status of an ADR.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
#[serde(rename_all = "lowercase")]
pub enum AdrStatus {
    /// ADR is proposed but not yet accepted.
    #[default]
    Proposed,
    /// ADR has been accepted.
    Accepted,
    /// ADR has been deprecated.
    Deprecated,
    /// ADR has been superseded by another ADR.
    Superseded,
    /// ADR has been rejected.
    Rejected,
}

impl std::fmt::Display for AdrStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Proposed => write!(f, "proposed"),
            Self::Accepted => write!(f, "accepted"),
            Self::Deprecated => write!(f, "deprecated"),
            Self::Superseded => write!(f, "superseded"),
            Self::Rejected => write!(f, "rejected"),
        }
    }
}

impl std::str::FromStr for AdrStatus {
    type Err = crate::Error;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "proposed" => Ok(Self::Proposed),
            "accepted" => Ok(Self::Accepted),
            "deprecated" => Ok(Self::Deprecated),
            "superseded" => Ok(Self::Superseded),
            "rejected" => Ok(Self::Rejected),
            _ => Err(crate::Error::InvalidStatus {
                status: s.to_string(),
                valid: vec![
                    "proposed".to_string(),
                    "accepted".to_string(),
                    "deprecated".to_string(),
                    "superseded".to_string(),
                    "rejected".to_string(),
                ],
            }),
        }
    }
}

/// Link to another ADR.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AdrLink {
    /// The type of link relationship.
    pub rel: String,
    /// The target ADR ID.
    pub target: String,
}

/// YAML frontmatter metadata for an ADR.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AdrFrontmatter {
    /// The ADR title.
    pub title: String,
    /// The current status.
    #[serde(default)]
    pub status: AdrStatus,
    /// Date when the ADR was created.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub date: Option<DateTime<Utc>>,
    /// Tags for categorization.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub tags: Vec<String>,
    /// Authors of the ADR.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub authors: Vec<String>,
    /// Decision makers/reviewers.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub deciders: Vec<String>,
    /// Links to other ADRs.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub links: Vec<AdrLink>,
    /// ADR format type.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub format: Option<String>,
    /// Custom fields.
    #[serde(flatten)]
    pub custom: HashMap<String, serde_yaml::Value>,
}

impl Default for AdrFrontmatter {
    fn default() -> Self {
        Self {
            title: String::new(),
            status: AdrStatus::default(),
            date: Some(Utc::now()),
            tags: Vec::new(),
            authors: Vec::new(),
            deciders: Vec::new(),
            links: Vec::new(),
            format: None,
            custom: HashMap::new(),
        }
    }
}

/// An Architecture Decision Record.
#[derive(Debug, Clone)]
pub struct Adr {
    /// Unique identifier (typically ADR-NNNN format).
    pub id: String,
    /// The git commit this ADR is attached to.
    pub commit: String,
    /// Frontmatter metadata.
    pub frontmatter: AdrFrontmatter,
    /// Markdown body content.
    pub body: String,
}

impl Adr {
    /// Create a new ADR with the given ID and title.
    #[must_use]
    pub fn new(id: String, title: String) -> Self {
        Self {
            id,
            commit: String::new(),
            frontmatter: AdrFrontmatter {
                title,
                ..Default::default()
            },
            body: String::new(),
        }
    }

    /// Parse an ADR from markdown content with YAML frontmatter.
    ///
    /// # Errors
    ///
    /// Returns an error if the frontmatter is invalid or missing.
    pub fn from_markdown(id: String, commit: String, content: &str) -> Result<Self, crate::Error> {
        let (frontmatter, body) = Self::parse_frontmatter(content)?;
        Ok(Self {
            id,
            commit,
            frontmatter,
            body,
        })
    }

    /// Parse YAML frontmatter from markdown content.
    fn parse_frontmatter(content: &str) -> Result<(AdrFrontmatter, String), crate::Error> {
        let content = content.trim();

        if !content.starts_with("---") {
            return Err(crate::Error::ParseError {
                message: "ADR must start with YAML frontmatter (---)".to_string(),
            });
        }

        let rest = &content[3..];
        let end_marker = rest.find("\n---");

        match end_marker {
            Some(pos) => {
                let yaml_content = &rest[..pos];
                let body = rest[pos + 4..].trim().to_string();

                let frontmatter: AdrFrontmatter =
                    serde_yaml::from_str(yaml_content).map_err(|e| crate::Error::ParseError {
                        message: format!("Invalid YAML frontmatter: {e}"),
                    })?;

                Ok((frontmatter, body))
            },
            None => Err(crate::Error::ParseError {
                message: "YAML frontmatter must be closed with ---".to_string(),
            }),
        }
    }

    /// Render the ADR as markdown with YAML frontmatter.
    ///
    /// # Errors
    ///
    /// Returns an error if serialization fails.
    pub fn to_markdown(&self) -> Result<String, crate::Error> {
        let yaml =
            serde_yaml::to_string(&self.frontmatter).map_err(|e| crate::Error::ParseError {
                message: format!("Failed to serialize frontmatter: {e}"),
            })?;

        Ok(format!("---\n{}---\n\n{}", yaml, self.body))
    }

    /// Get the ADR title.
    #[must_use]
    pub fn title(&self) -> &str {
        &self.frontmatter.title
    }

    /// Get the ADR status.
    #[must_use]
    pub const fn status(&self) -> &AdrStatus {
        &self.frontmatter.status
    }

    /// Check if this ADR has the given tag.
    #[must_use]
    pub fn has_tag(&self, tag: &str) -> bool {
        self.frontmatter
            .tags
            .iter()
            .any(|t| t.eq_ignore_ascii_case(tag))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_status_display() {
        assert_eq!(AdrStatus::Proposed.to_string(), "proposed");
        assert_eq!(AdrStatus::Accepted.to_string(), "accepted");
    }

    #[test]
    fn test_status_parse() {
        assert_eq!(
            "proposed".parse::<AdrStatus>().unwrap(),
            AdrStatus::Proposed
        );
        assert_eq!(
            "ACCEPTED".parse::<AdrStatus>().unwrap(),
            AdrStatus::Accepted
        );
    }

    #[test]
    fn test_adr_from_markdown() {
        let content = r#"---
title: Use Rust for CLI
status: proposed
tags:
  - architecture
  - rust
---

## Context

We need to decide on a language for the CLI.
"#;

        let adr =
            Adr::from_markdown("ADR-0001".to_string(), "abc123".to_string(), content).unwrap();
        assert_eq!(adr.title(), "Use Rust for CLI");
        assert_eq!(*adr.status(), AdrStatus::Proposed);
        assert!(adr.has_tag("rust"));
    }
}
