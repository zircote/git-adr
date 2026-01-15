//! Export ADRs to various formats.

use anyhow::Result;
use clap::Args as ClapArgs;
use colored::Colorize;
use std::fmt::Write;
use std::fs;
use std::path::Path;

use crate::core::{AdrStatus, ConfigManager, Git, NotesManager};

/// Arguments for the export command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// Output directory.
    #[arg(long, short, default_value = "./adr-export")]
    pub output: String,

    /// Export format (markdown, json, html).
    #[arg(long, short, default_value = "markdown")]
    pub format: String,

    /// Filter by status.
    #[arg(long)]
    pub status: Option<String>,

    /// Filter by tag.
    #[arg(long)]
    pub tag: Option<String>,

    /// Generate index file.
    #[arg(long, default_value = "true")]
    pub index: bool,
}

/// Run the export command.
///
/// # Errors
///
/// Returns an error if export fails.
#[allow(clippy::too_many_lines)]
pub fn run(args: Args) -> Result<()> {
    let git = Git::new();
    git.check_repository()?;

    let config = ConfigManager::new(git.clone()).load()?;
    let notes = NotesManager::new(git, config);

    let mut adrs = notes.list()?;

    // Filter by status
    if let Some(status_str) = &args.status {
        let status: AdrStatus = status_str
            .parse()
            .map_err(|e| anyhow::anyhow!("{}", e))?;
        adrs.retain(|a| a.frontmatter.status == status);
    }

    // Filter by tag
    if let Some(tag) = &args.tag {
        adrs.retain(|a| a.frontmatter.tags.iter().any(|t| t.contains(tag)));
    }

    if adrs.is_empty() {
        eprintln!("{} No ADRs to export", "!".yellow());
        return Ok(());
    }

    eprintln!(
        "{} Exporting {} ADR(s) to {} format in {}",
        "→".blue(),
        adrs.len(),
        args.format.cyan(),
        args.output.cyan()
    );

    // Create output directory
    let output_path = Path::new(&args.output);
    fs::create_dir_all(output_path)?;

    let extension = if args.format == "json" {
        "json"
    } else if args.format == "html" {
        "html"
    } else {
        "md"
    };

    // Export each ADR
    for adr in &adrs {
        let filename = format!("{}.{}", adr.id, extension);
        let filepath = output_path.join(&filename);

        let content = if args.format == "json" {
            let json = serde_json::json!({
                "id": adr.id,
                "title": adr.frontmatter.title,
                "status": adr.frontmatter.status.to_string(),
                "date": adr.frontmatter.date.as_ref().map(|d| d.datetime().to_rfc3339()),
                "tags": adr.frontmatter.tags,
                "authors": adr.frontmatter.authors,
                "deciders": adr.frontmatter.deciders,
                "commit": adr.commit,
                "body": adr.body,
            });
            serde_json::to_string_pretty(&json)?
        } else if args.format == "html" {
            export_html_single(adr)?
        } else {
            adr.to_markdown()?
        };

        fs::write(&filepath, content)?;
        eprintln!("  {} {}", "✓".green(), filename);
    }

    // Generate index file
    if args.index {
        let index_filename = format!("index.{}", extension);
        let index_path = output_path.join(&index_filename);

        let index_content = if args.format == "json" {
            export_json_index(&adrs)?
        } else if args.format == "html" {
            export_html_index(&adrs)
        } else {
            export_markdown_index(&adrs)
        };

        fs::write(&index_path, index_content)?;
        eprintln!("  {} {}", "✓".green(), index_filename);
    }

    eprintln!(
        "{} Exported {} ADR(s) to {}",
        "✓".green(),
        adrs.len(),
        args.output.cyan()
    );

    Ok(())
}

/// Export a single ADR to HTML.
fn export_html_single(adr: &crate::core::Adr) -> Result<String> {
    let tags_html = if adr.frontmatter.tags.is_empty() {
        String::new()
    } else {
        let tags = adr
            .frontmatter
            .tags
            .iter()
            .fold(String::new(), |mut acc, t| {
                let _ = write!(acc, "<span class=\"tag\">{}</span>", html_escape(t));
                acc
            });
        format!("<div class=\"tags\">{tags}</div>")
    };

    Ok(format!(
        r#"<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{} - {}</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; }}
        .status {{ display: inline-block; padding: 0.25rem 0.5rem; border-radius: 4px; background: #e0e0e0; }}
        .status.accepted {{ background: #c8e6c9; }}
        .status.rejected {{ background: #ffcdd2; }}
        .status.superseded {{ background: #fff9c4; }}
        .tags {{ margin: 1rem 0; }}
        .tag {{ display: inline-block; padding: 0.25rem 0.5rem; margin-right: 0.5rem; border-radius: 4px; background: #e3f2fd; }}
        pre {{ background: #f5f5f5; padding: 1rem; overflow-x: auto; }}
    </style>
</head>
<body>
    <h1>{}</h1>
    <p><span class="status {}">{}</span></p>
    {}
    <hr>
    {}
</body>
</html>"#,
        adr.id,
        html_escape(&adr.frontmatter.title),
        html_escape(&adr.frontmatter.title),
        adr.frontmatter.status,
        adr.frontmatter.status,
        tags_html,
        markdown_to_html(&adr.body)
    ))
}

/// Export JSON index.
fn export_json_index(adrs: &[crate::core::Adr]) -> Result<String> {
    let index: Vec<_> = adrs
        .iter()
        .map(|adr| {
            serde_json::json!({
                "id": adr.id,
                "title": adr.frontmatter.title,
                "status": adr.frontmatter.status.to_string(),
                "date": adr.frontmatter.date.as_ref().map(|d| d.datetime().to_rfc3339()),
                "tags": adr.frontmatter.tags,
            })
        })
        .collect();
    Ok(serde_json::to_string_pretty(&index)?)
}

/// Export HTML index.
fn export_html_index(adrs: &[crate::core::Adr]) -> String {
    let mut items = String::new();
    for adr in adrs {
        let _ = write!(
            items,
            "<tr><td><a href=\"{}.html\">{}</a></td><td>{}</td><td>{}</td><td>{}</td></tr>",
            adr.id,
            adr.id,
            html_escape(&adr.frontmatter.title),
            adr.frontmatter.status,
            adr.frontmatter.tags.join(", ")
        );
    }

    format!(
        r#"<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>ADR Index</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 1000px; margin: 0 auto; padding: 2rem; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ text-align: left; padding: 0.5rem; border-bottom: 1px solid #ddd; }}
        th {{ background: #f5f5f5; }}
        a {{ color: #1976d2; }}
    </style>
</head>
<body>
    <h1>Architecture Decision Records</h1>
    <table>
        <thead>
            <tr><th>ID</th><th>Title</th><th>Status</th><th>Tags</th></tr>
        </thead>
        <tbody>
            {items}
        </tbody>
    </table>
</body>
</html>"#
    )
}

/// Export markdown index.
fn export_markdown_index(adrs: &[crate::core::Adr]) -> String {
    let mut content = String::from("# Architecture Decision Records\n\n");
    content.push_str("| ID | Title | Status | Tags |\n");
    content.push_str("|-----|-------|--------|------|\n");
    for adr in adrs {
        let _ = writeln!(
            content,
            "| [{}]({}.md) | {} | {} | {} |",
            adr.id,
            adr.id,
            adr.frontmatter.title,
            adr.frontmatter.status,
            adr.frontmatter.tags.join(", ")
        );
    }
    content
}

/// Escape HTML special characters.
fn html_escape(s: &str) -> String {
    s.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&#39;")
}

/// Simple markdown to HTML conversion (basic support).
fn markdown_to_html(md: &str) -> String {
    let mut html = String::new();
    let mut in_code_block = false;

    for line in md.lines() {
        if line.starts_with("```") {
            if in_code_block {
                html.push_str("</code></pre>\n");
                in_code_block = false;
            } else {
                html.push_str("<pre><code>");
                in_code_block = true;
            }
            continue;
        }

        if in_code_block {
            html.push_str(&html_escape(line));
            html.push('\n');
            continue;
        }

        let line = line.trim();

        if line.is_empty() {
            html.push_str("<p></p>\n");
        } else if let Some(heading) = line.strip_prefix("### ") {
            let _ = writeln!(html, "<h3>{}</h3>", html_escape(heading));
        } else if let Some(heading) = line.strip_prefix("## ") {
            let _ = writeln!(html, "<h2>{}</h2>", html_escape(heading));
        } else if let Some(heading) = line.strip_prefix("# ") {
            let _ = writeln!(html, "<h1>{}</h1>", html_escape(heading));
        } else if let Some(item) = line.strip_prefix("- ").or_else(|| line.strip_prefix("* ")) {
            let _ = writeln!(html, "<li>{}</li>", html_escape(item));
        } else {
            let _ = writeln!(html, "<p>{}</p>", html_escape(line));
        }
    }

    if in_code_block {
        html.push_str("</code></pre>\n");
    }

    html
}
