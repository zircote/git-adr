//! JSON export functionality.

use crate::core::Adr;
use crate::export::{ExportResult, Exporter};
use crate::Error;
use serde::Serialize;
use std::path::Path;

/// JSON exporter.
#[derive(Debug, Default)]
pub struct JsonExporter {
    /// Pretty print JSON output.
    pub pretty: bool,
}

impl JsonExporter {
    /// Create a new JSON exporter.
    #[must_use]
    pub fn new() -> Self {
        Self { pretty: true }
    }

    /// Disable pretty printing.
    #[must_use]
    pub fn compact(mut self) -> Self {
        self.pretty = false;
        self
    }
}

/// JSON representation of an ADR.
#[derive(Debug, Serialize)]
struct AdrJson<'a> {
    id: &'a str,
    commit: &'a str,
    title: &'a str,
    status: String,
    date: Option<String>,
    tags: &'a [String],
    authors: &'a [String],
    deciders: &'a [String],
    body: &'a str,
}

impl<'a> AdrJson<'a> {
    fn from_adr(adr: &'a Adr) -> Self {
        Self {
            id: &adr.id,
            commit: &adr.commit,
            title: &adr.frontmatter.title,
            status: adr.frontmatter.status.to_string(),
            date: adr.frontmatter.date.as_ref().map(|d| d.datetime().to_rfc3339()),
            tags: &adr.frontmatter.tags,
            authors: &adr.frontmatter.authors,
            deciders: &adr.frontmatter.deciders,
            body: &adr.body,
        }
    }
}

impl Exporter for JsonExporter {
    fn export(&self, adr: &Adr, path: &Path) -> Result<(), Error> {
        let json_adr = AdrJson::from_adr(adr);

        let content = if self.pretty {
            serde_json::to_string_pretty(&json_adr)
        } else {
            serde_json::to_string(&json_adr)
        }
        .map_err(|e| Error::ExportError {
            message: format!("Failed to serialize ADR: {e}"),
        })?;

        std::fs::write(path, content).map_err(|e| Error::IoError {
            message: format!("Failed to write {}: {e}", path.display()),
        })
    }

    fn export_all(&self, adrs: &[Adr], dir: &Path) -> Result<ExportResult, Error> {
        std::fs::create_dir_all(dir).map_err(|e| Error::IoError {
            message: format!("Failed to create directory {}: {e}", dir.display()),
        })?;

        let mut result = ExportResult::default();

        // Export individual files
        for adr in adrs {
            let path = dir.join(format!("{}.json", adr.id));
            match self.export(adr, &path) {
                Ok(()) => {
                    result.exported += 1;
                    result.files.push(path.display().to_string());
                },
                Err(e) => {
                    result.errors.push(format!("{}: {e}", adr.id));
                },
            }
        }

        // Export combined file
        let all_path = dir.join("all.json");
        let all_json: Vec<AdrJson> = adrs.iter().map(AdrJson::from_adr).collect();

        let content = if self.pretty {
            serde_json::to_string_pretty(&all_json)
        } else {
            serde_json::to_string(&all_json)
        }
        .map_err(|e| Error::ExportError {
            message: format!("Failed to serialize ADRs: {e}"),
        })?;

        std::fs::write(&all_path, content).map_err(|e| Error::IoError {
            message: format!("Failed to write {}: {e}", all_path.display()),
        })?;

        result.files.push(all_path.display().to_string());

        Ok(result)
    }
}
