//! DOCX export functionality.

use crate::core::Adr;
use crate::export::{ExportResult, Exporter};
use crate::Error;
use std::path::Path;

/// DOCX exporter.
#[derive(Debug, Default)]
pub struct DocxExporter {
    /// Include frontmatter in output.
    pub include_frontmatter: bool,
}

impl DocxExporter {
    /// Create a new DOCX exporter.
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    /// Include frontmatter in the exported document.
    #[must_use]
    pub fn with_frontmatter(mut self) -> Self {
        self.include_frontmatter = true;
        self
    }
}

impl Exporter for DocxExporter {
    fn export(&self, adr: &Adr, path: &Path) -> Result<(), Error> {
        // TODO: Implement using docx-rs when feature is enabled
        let _ = adr;
        let _ = path;
        Err(Error::ExportError {
            message: "DOCX export not yet implemented".to_string(),
        })
    }

    fn export_all(&self, adrs: &[Adr], dir: &Path) -> Result<ExportResult, Error> {
        std::fs::create_dir_all(dir).map_err(|e| Error::IoError {
            message: format!("Failed to create directory {}: {e}", dir.display()),
        })?;

        let mut result = ExportResult::default();

        for adr in adrs {
            let path = dir.join(format!("{}.docx", adr.id));
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

        Ok(result)
    }
}
