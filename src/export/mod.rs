//! Export functionality for git-adr.
//!
//! This module provides export capabilities:
//! - DOCX export
//! - HTML export
//! - JSON export

use crate::core::Adr;
use crate::Error;
use std::path::Path;

mod docx;
mod html;
mod json;

pub use self::docx::DocxExporter;
pub use self::html::HtmlExporter;
pub use self::json::JsonExporter;

/// Export format.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ExportFormat {
    /// DOCX (Microsoft Word) format.
    Docx,
    /// HTML format.
    Html,
    /// JSON format.
    Json,
    /// Markdown format.
    Markdown,
}

impl std::fmt::Display for ExportFormat {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Docx => write!(f, "docx"),
            Self::Html => write!(f, "html"),
            Self::Json => write!(f, "json"),
            Self::Markdown => write!(f, "markdown"),
        }
    }
}

impl std::str::FromStr for ExportFormat {
    type Err = Error;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "docx" | "word" => Ok(Self::Docx),
            "html" => Ok(Self::Html),
            "json" => Ok(Self::Json),
            "markdown" | "md" => Ok(Self::Markdown),
            _ => Err(Error::InvalidFormat {
                format: s.to_string(),
            }),
        }
    }
}

/// Exporter trait for different formats.
pub trait Exporter {
    /// Export a single ADR to the given path.
    ///
    /// # Errors
    ///
    /// Returns an error if export fails.
    fn export(&self, adr: &Adr, path: &Path) -> Result<(), Error>;

    /// Export multiple ADRs to a directory.
    ///
    /// # Errors
    ///
    /// Returns an error if export fails.
    fn export_all(&self, adrs: &[Adr], dir: &Path) -> Result<ExportResult, Error>;
}

/// Result of an export operation.
#[derive(Debug, Default)]
pub struct ExportResult {
    /// Number of files exported.
    pub exported: usize,
    /// Paths to exported files.
    pub files: Vec<String>,
    /// Errors encountered.
    pub errors: Vec<String>,
}

/// Export ADRs to the specified format.
///
/// # Errors
///
/// Returns an error if export fails.
pub fn export_adrs(adrs: &[Adr], dir: &Path, format: ExportFormat) -> Result<ExportResult, Error> {
    match format {
        ExportFormat::Docx => DocxExporter::new().export_all(adrs, dir),
        ExportFormat::Html => HtmlExporter::new().export_all(adrs, dir),
        ExportFormat::Json => JsonExporter::new().export_all(adrs, dir),
        ExportFormat::Markdown => {
            // Markdown export is just copying the original content
            let mut result = ExportResult::default();
            for adr in adrs {
                let path = dir.join(format!("{}.md", adr.id));
                let content = adr.to_markdown()?;
                std::fs::write(&path, content).map_err(|e| Error::IoError {
                    message: format!("Failed to write {}: {e}", path.display()),
                })?;
                result.exported += 1;
                result.files.push(path.display().to_string());
            }
            Ok(result)
        },
    }
}
