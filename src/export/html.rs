//! HTML export functionality.

use crate::core::Adr;
use crate::export::{ExportResult, Exporter};
use crate::Error;
use std::path::Path;

/// HTML exporter.
#[derive(Debug, Default)]
pub struct HtmlExporter {
    /// Include CSS styling.
    pub include_style: bool,
    /// Generate index page.
    pub generate_index: bool,
}

impl HtmlExporter {
    /// Create a new HTML exporter.
    #[must_use]
    pub fn new() -> Self {
        Self {
            include_style: true,
            generate_index: true,
        }
    }

    /// Disable inline CSS styling.
    #[must_use]
    pub fn without_style(mut self) -> Self {
        self.include_style = false;
        self
    }

    /// Disable index page generation.
    #[must_use]
    pub fn without_index(mut self) -> Self {
        self.generate_index = false;
        self
    }

    /// Generate HTML from markdown content.
    fn markdown_to_html(&self, content: &str) -> String {
        // Simple markdown to HTML conversion
        // TODO: Use a proper markdown parser
        content
            .lines()
            .map(|line| {
                if let Some(rest) = line.strip_prefix("# ") {
                    format!("<h1>{rest}</h1>")
                } else if let Some(rest) = line.strip_prefix("## ") {
                    format!("<h2>{rest}</h2>")
                } else if let Some(rest) = line.strip_prefix("### ") {
                    format!("<h3>{rest}</h3>")
                } else if let Some(rest) = line.strip_prefix("- ") {
                    format!("<li>{rest}</li>")
                } else if line.is_empty() {
                    String::new()
                } else {
                    format!("<p>{line}</p>")
                }
            })
            .collect::<Vec<_>>()
            .join("\n")
    }

    /// Generate the CSS style.
    fn css_style(&self) -> &'static str {
        r#"
<style>
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
    line-height: 1.6;
}
h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 0.5rem; }
h2 { color: #34495e; margin-top: 2rem; }
h3 { color: #7f8c8d; }
.status {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-size: 0.875rem;
    font-weight: 500;
}
.status-proposed { background: #f39c12; color: white; }
.status-accepted { background: #27ae60; color: white; }
.status-deprecated { background: #95a5a6; color: white; }
.status-superseded { background: #9b59b6; color: white; }
.status-rejected { background: #e74c3c; color: white; }
.tags { margin-top: 1rem; }
.tag {
    display: inline-block;
    padding: 0.2rem 0.5rem;
    background: #ecf0f1;
    border-radius: 3px;
    font-size: 0.8rem;
    margin-right: 0.5rem;
}
</style>
"#
    }
}

impl Exporter for HtmlExporter {
    fn export(&self, adr: &Adr, path: &Path) -> Result<(), Error> {
        let status_class = format!("status-{}", adr.frontmatter.status);
        let body_html = self.markdown_to_html(&adr.body);

        let tags_html = if adr.frontmatter.tags.is_empty() {
            String::new()
        } else {
            let tags: Vec<String> = adr
                .frontmatter
                .tags
                .iter()
                .map(|t| format!("<span class=\"tag\">{t}</span>"))
                .collect();
            format!("<div class=\"tags\">{}</div>", tags.join(""))
        };

        let style = if self.include_style {
            self.css_style()
        } else {
            ""
        };

        let html = format!(
            r#"<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{} - {}</title>
    {style}
</head>
<body>
    <article>
        <header>
            <h1>{}</h1>
            <span class="status {status_class}">{}</span>
            {tags_html}
        </header>
        <main>
            {body_html}
        </main>
    </article>
</body>
</html>"#,
            adr.id, adr.frontmatter.title, adr.frontmatter.title, adr.frontmatter.status
        );

        std::fs::write(path, html).map_err(|e| Error::IoError {
            message: format!("Failed to write {}: {e}", path.display()),
        })
    }

    fn export_all(&self, adrs: &[Adr], dir: &Path) -> Result<ExportResult, Error> {
        std::fs::create_dir_all(dir).map_err(|e| Error::IoError {
            message: format!("Failed to create directory {}: {e}", dir.display()),
        })?;

        let mut result = ExportResult::default();

        for adr in adrs {
            let path = dir.join(format!("{}.html", adr.id));
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

        // Generate index if requested
        if self.generate_index && !adrs.is_empty() {
            let index_path = dir.join("index.html");
            if let Err(e) = self.generate_index_page(adrs, &index_path) {
                result.errors.push(format!("index: {e}"));
            } else {
                result.files.push(index_path.display().to_string());
            }
        }

        Ok(result)
    }
}

impl HtmlExporter {
    /// Generate an index page linking to all ADRs.
    fn generate_index_page(&self, adrs: &[Adr], path: &Path) -> Result<(), Error> {
        let style = if self.include_style {
            self.css_style()
        } else {
            ""
        };

        let rows: Vec<String> = adrs
            .iter()
            .map(|adr| {
                let status_class = format!("status-{}", adr.frontmatter.status);
                format!(
                    r#"<tr>
                <td><a href="{}.html">{}</a></td>
                <td>{}</td>
                <td><span class="status {status_class}">{}</span></td>
            </tr>"#,
                    adr.id, adr.id, adr.frontmatter.title, adr.frontmatter.status
                )
            })
            .collect();

        let html = format!(
            r#"<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Architecture Decision Records</title>
    {style}
    <style>
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid #ecf0f1; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        tr:hover {{ background: #f8f9fa; }}
        a {{ color: #3498db; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>Architecture Decision Records</h1>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {}
        </tbody>
    </table>
</body>
</html>"#,
            rows.join("\n")
        );

        std::fs::write(path, html).map_err(|e| Error::IoError {
            message: format!("Failed to write {}: {e}", path.display()),
        })
    }
}
