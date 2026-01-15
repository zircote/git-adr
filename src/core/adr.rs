//! ADR data model.
//!
//! This module defines the core ADR structure that represents an
//! Architecture Decision Record with its metadata and content.

use chrono::{DateTime, NaiveDate, Utc};
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use std::collections::HashMap;

/// Flexible date type that accepts both full datetime and date-only formats.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FlexibleDate(pub DateTime<Utc>);

impl FlexibleDate {
    /// Get the inner `DateTime<Utc>` value.
    #[must_use]
    pub const fn datetime(&self) -> DateTime<Utc> {
        self.0
    }
}

impl From<DateTime<Utc>> for FlexibleDate {
    fn from(dt: DateTime<Utc>) -> Self {
        Self(dt)
    }
}

impl Serialize for FlexibleDate {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        // Serialize as YYYY-MM-DD format
        serializer.serialize_str(&self.0.format("%Y-%m-%d").to_string())
    }
}

impl<'de> Deserialize<'de> for FlexibleDate {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;

        // Try RFC3339 format first (e.g., "2025-12-15T00:00:00Z")
        if let Ok(dt) = DateTime::parse_from_rfc3339(&s) {
            return Ok(Self(dt.with_timezone(&Utc)));
        }

        // Try YYYY-MM-DD format (e.g., "2025-12-15")
        if let Ok(date) = NaiveDate::parse_from_str(&s, "%Y-%m-%d") {
            if let Some(datetime) = date.and_hms_opt(0, 0, 0) {
                return Ok(Self(datetime.and_utc()));
            }
        }

        Err(serde::de::Error::custom(format!(
            "invalid date format: {}. Expected YYYY-MM-DD or RFC3339.",
            s
        )))
    }
}

/// Status of an ADR.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize, Default)]
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
    /// The ADR ID (optional in frontmatter, may be stored separately).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub id: Option<String>,
    /// The ADR title.
    pub title: String,
    /// The current status.
    #[serde(default)]
    pub status: AdrStatus,
    /// Date when the ADR was created.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub date: Option<FlexibleDate>,
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
    /// ID of ADR that this one supersedes.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub supersedes: Option<String>,
    /// ID of ADR that superseded this one.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub superseded_by: Option<String>,
    /// Custom fields.
    #[serde(flatten)]
    pub custom: HashMap<String, serde_yaml::Value>,
}

impl Default for AdrFrontmatter {
    fn default() -> Self {
        Self {
            id: None,
            title: String::new(),
            status: AdrStatus::default(),
            date: Some(FlexibleDate(Utc::now())),
            tags: Vec::new(),
            authors: Vec::new(),
            deciders: Vec::new(),
            links: Vec::new(),
            format: None,
            supersedes: None,
            superseded_by: None,
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
            id: id.clone(),
            commit: String::new(),
            frontmatter: AdrFrontmatter {
                id: Some(id),
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
    use chrono::Datelike;

    #[test]
    fn test_status_display() {
        assert_eq!(AdrStatus::Proposed.to_string(), "proposed");
        assert_eq!(AdrStatus::Accepted.to_string(), "accepted");
        assert_eq!(AdrStatus::Deprecated.to_string(), "deprecated");
        assert_eq!(AdrStatus::Superseded.to_string(), "superseded");
        assert_eq!(AdrStatus::Rejected.to_string(), "rejected");
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
        assert_eq!(
            "Deprecated".parse::<AdrStatus>().unwrap(),
            AdrStatus::Deprecated
        );
        assert_eq!(
            "SUPERSEDED".parse::<AdrStatus>().unwrap(),
            AdrStatus::Superseded
        );
        assert_eq!(
            "rejected".parse::<AdrStatus>().unwrap(),
            AdrStatus::Rejected
        );
    }

    #[test]
    fn test_status_parse_invalid() {
        let result = "invalid".parse::<AdrStatus>();
        assert!(result.is_err());
    }

    #[test]
    fn test_status_default() {
        let status = AdrStatus::default();
        assert_eq!(status, AdrStatus::Proposed);
    }

    #[test]
    fn test_adr_new() {
        let adr = Adr::new("ADR-0001".to_string(), "Test Title".to_string());
        assert_eq!(adr.id, "ADR-0001");
        assert_eq!(adr.title(), "Test Title");
        assert_eq!(*adr.status(), AdrStatus::Proposed);
        assert!(adr.commit.is_empty());
        assert!(adr.body.is_empty());
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
        assert!(adr.has_tag("architecture"));
        assert!(!adr.has_tag("python"));
    }

    #[test]
    fn test_adr_from_markdown_with_date() {
        // Test the actual format used in git notes
        let content = r#"---
date: '2025-12-15'
format: nygard
id: 00000000-use-adrs
status: accepted
tags:
- documentation
- process
title: Use Architecture Decision Records
---

# Use Architecture Decision Records

## Status

accepted
"#;

        let adr = Adr::from_markdown("ADR-0000".to_string(), "abc123".to_string(), content)
            .expect("Failed to parse ADR");
        assert_eq!(adr.title(), "Use Architecture Decision Records");
        assert_eq!(*adr.status(), AdrStatus::Accepted);
    }

    #[test]
    fn test_adr_from_markdown_no_frontmatter() {
        let content = "No frontmatter here";
        let result = Adr::from_markdown("ADR-0001".to_string(), "abc123".to_string(), content);
        assert!(result.is_err());
    }

    #[test]
    fn test_adr_from_markdown_unclosed_frontmatter() {
        let content = r#"---
title: Unclosed
status: proposed
No closing marker
"#;
        let result = Adr::from_markdown("ADR-0001".to_string(), "abc123".to_string(), content);
        assert!(result.is_err());
    }

    #[test]
    fn test_adr_to_markdown() {
        let mut adr = Adr::new("ADR-0001".to_string(), "Test Title".to_string());
        adr.body = "Body content here.".to_string();

        let markdown = adr.to_markdown().expect("Should serialize");
        assert!(markdown.contains("---"));
        assert!(markdown.contains("title: Test Title"));
        assert!(markdown.contains("Body content here."));
    }

    #[test]
    fn test_adr_has_tag_case_insensitive() {
        let mut adr = Adr::new("ADR-0001".to_string(), "Test".to_string());
        adr.frontmatter.tags = vec!["Architecture".to_string()];

        assert!(adr.has_tag("architecture"));
        assert!(adr.has_tag("ARCHITECTURE"));
        assert!(adr.has_tag("Architecture"));
    }

    #[test]
    fn test_flexible_date_from_datetime() {
        let now = Utc::now();
        let flexible = FlexibleDate::from(now);
        assert_eq!(flexible.datetime(), now);
    }

    #[test]
    fn test_adr_frontmatter_default() {
        let fm = AdrFrontmatter::default();
        assert!(fm.id.is_none());
        assert!(fm.title.is_empty());
        assert_eq!(fm.status, AdrStatus::Proposed);
        assert!(fm.tags.is_empty());
        assert!(fm.authors.is_empty());
        assert!(fm.deciders.is_empty());
        assert!(fm.links.is_empty());
    }

    #[test]
    fn test_adr_link() {
        let link = AdrLink {
            rel: "supersedes".to_string(),
            target: "ADR-0001".to_string(),
        };
        assert_eq!(link.rel, "supersedes");
        assert_eq!(link.target, "ADR-0001");
    }

    #[test]
    fn test_flexible_date_serialize() {
        use chrono::TimeZone;
        let date = chrono::Utc.with_ymd_and_hms(2025, 12, 15, 0, 0, 0).unwrap();
        let flexible = FlexibleDate(date);
        let serialized = serde_yaml::to_string(&flexible).unwrap();
        assert!(serialized.contains("2025-12-15"));
    }

    #[test]
    fn test_flexible_date_deserialize_rfc3339() {
        let yaml = "2025-12-15T00:00:00Z";
        let result: FlexibleDate = serde_yaml::from_str(yaml).unwrap();
        assert_eq!(result.0.year(), 2025);
        assert_eq!(result.0.month(), 12);
        assert_eq!(result.0.day(), 15);
    }

    #[test]
    fn test_flexible_date_deserialize_date_only() {
        let yaml = "2025-12-15";
        let result: FlexibleDate = serde_yaml::from_str(yaml).unwrap();
        assert_eq!(result.0.year(), 2025);
        assert_eq!(result.0.month(), 12);
        assert_eq!(result.0.day(), 15);
    }

    #[test]
    fn test_flexible_date_deserialize_invalid() {
        let yaml = "invalid-date-format";
        let result: Result<FlexibleDate, _> = serde_yaml::from_str(yaml);
        assert!(result.is_err());
    }

    #[test]
    fn test_adr_from_markdown_invalid_yaml() {
        let content = r#"---
title: [invalid yaml
status: proposed
---

Body
"#;
        let result = Adr::from_markdown("ADR-0001".to_string(), "abc123".to_string(), content);
        assert!(result.is_err());
    }

    #[test]
    fn test_adr_frontmatter_with_all_fields() {
        let content = r#"---
id: ADR-0001
title: Test ADR
status: accepted
date: 2025-12-15
tags:
  - test
  - example
authors:
  - Alice
deciders:
  - Bob
links:
  - rel: supersedes
    target: ADR-0000
format: nygard
supersedes: ADR-0000
superseded_by: ADR-0002
custom_field: custom_value
---

Body content
"#;
        let adr = Adr::from_markdown("ADR-0001".to_string(), "abc123".to_string(), content)
            .expect("Should parse");
        assert_eq!(adr.frontmatter.id, Some("ADR-0001".to_string()));
        assert_eq!(adr.frontmatter.authors, vec!["Alice"]);
        assert_eq!(adr.frontmatter.deciders, vec!["Bob"]);
        assert_eq!(adr.frontmatter.format, Some("nygard".to_string()));
        assert_eq!(adr.frontmatter.supersedes, Some("ADR-0000".to_string()));
        assert_eq!(adr.frontmatter.superseded_by, Some("ADR-0002".to_string()));
        assert!(adr.frontmatter.custom.contains_key("custom_field"));
    }

    #[test]
    fn test_status_hash() {
        use std::collections::HashSet;
        let mut set = HashSet::new();
        set.insert(AdrStatus::Proposed);
        set.insert(AdrStatus::Accepted);
        assert_eq!(set.len(), 2);
        set.insert(AdrStatus::Proposed);
        assert_eq!(set.len(), 2); // Same status, no increase
    }
}
