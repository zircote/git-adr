//! Import ADRs from files.

use anyhow::Result;
use clap::Args as ClapArgs;
use colored::Colorize;
use std::fs;
use std::path::Path;

use crate::core::{Adr, AdrStatus, ConfigManager, Git, NotesManager};

/// Arguments for the import command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// Path to import from (file or directory).
    pub path: String,

    /// Import format (auto, markdown, json, adr-tools).
    #[arg(long, short, default_value = "auto")]
    pub format: String,

    /// Link ADRs to commits by date.
    #[arg(long)]
    pub link_by_date: bool,

    /// Preview import without saving.
    #[arg(long)]
    pub dry_run: bool,
}

/// Run the import command.
///
/// # Errors
///
/// Returns an error if import fails.
pub fn run(args: Args) -> Result<()> {
    let git = Git::new();
    git.check_repository()?;

    let config = ConfigManager::new(git.clone()).load()?;
    let notes = NotesManager::new(git, config.clone());

    let path = Path::new(&args.path);

    if !path.exists() {
        anyhow::bail!("Path not found: {}", args.path);
    }

    let files = if path.is_dir() {
        // Find markdown files in directory
        find_adr_files(path)?
    } else {
        vec![path.to_path_buf()]
    };

    if files.is_empty() {
        eprintln!("{} No ADR files found to import", "!".yellow());
        return Ok(());
    }

    eprintln!(
        "{} Found {} file(s) to import",
        "→".blue(),
        files.len().to_string().cyan()
    );

    let mut imported = 0;
    let mut skipped = 0;

    for file in &files {
        match import_file(file, &args, &notes, &config) {
            Ok(adr) => {
                if args.dry_run {
                    eprintln!(
                        "  {} Would import: {} - {}",
                        "→".blue(),
                        adr.id.cyan(),
                        adr.frontmatter.title
                    );
                } else {
                    eprintln!(
                        "  {} Imported: {} - {}",
                        "✓".green(),
                        adr.id.cyan(),
                        adr.frontmatter.title
                    );
                }
                imported += 1;
            }
            Err(e) => {
                eprintln!(
                    "  {} Skipped {}: {}",
                    "!".yellow(),
                    file.display(),
                    e
                );
                skipped += 1;
            }
        }
    }

    eprintln!();
    if args.dry_run {
        eprintln!(
            "{} Dry run complete: {} would be imported, {} would be skipped",
            "→".blue(),
            imported.to_string().green(),
            skipped.to_string().yellow()
        );
    } else {
        eprintln!(
            "{} Import complete: {} imported, {} skipped",
            "✓".green(),
            imported.to_string().green(),
            skipped.to_string().yellow()
        );
    }

    Ok(())
}

/// Find ADR files in a directory.
fn find_adr_files(dir: &Path) -> Result<Vec<std::path::PathBuf>> {
    let mut files = Vec::new();

    for entry in fs::read_dir(dir)? {
        let entry = entry?;
        let path = entry.path();

        if path.is_file() {
            let ext = path.extension().and_then(|s| s.to_str()).unwrap_or("");
            if ext == "md" || ext == "markdown" || ext == "json" {
                files.push(path);
            }
        }
    }

    // Sort by filename for consistent ordering
    files.sort();

    Ok(files)
}

/// Import a single file.
fn import_file(
    path: &Path,
    args: &Args,
    notes: &NotesManager,
    config: &crate::core::AdrConfig,
) -> Result<Adr> {
    let content = fs::read_to_string(path)?;
    let format = detect_format(path, &args.format, &content);

    let adr = match format.as_str() {
        "json" => import_json(&content)?,
        "adr-tools" => import_adr_tools(path, &content, config, notes)?,
        _ => import_markdown(&content, config, notes)?,
    };

    if !args.dry_run {
        notes.create(&adr)?;
    }

    Ok(adr)
}

/// Detect file format.
fn detect_format(path: &Path, hint: &str, content: &str) -> String {
    if hint != "auto" {
        return hint.to_string();
    }

    let ext = path.extension().and_then(|s| s.to_str()).unwrap_or("");

    if ext == "json" {
        return "json".to_string();
    }

    // Check for adr-tools format (numbered prefix like "0001-")
    let filename = path.file_stem().and_then(|s| s.to_str()).unwrap_or("");
    if filename.len() >= 5 && filename[..4].chars().all(|c| c.is_ascii_digit()) {
        return "adr-tools".to_string();
    }

    // Check for YAML frontmatter
    if content.trim_start().starts_with("---") {
        return "markdown".to_string();
    }

    "markdown".to_string()
}

/// Import from JSON format.
fn import_json(content: &str) -> Result<Adr> {
    let data: serde_json::Value = serde_json::from_str(content)?;

    let id = data["id"]
        .as_str()
        .ok_or_else(|| anyhow::anyhow!("Missing 'id' field"))?
        .to_string();

    let title = data["title"]
        .as_str()
        .ok_or_else(|| anyhow::anyhow!("Missing 'title' field"))?
        .to_string();

    let status_str = data["status"]
        .as_str()
        .unwrap_or("proposed");
    let status: AdrStatus = status_str.parse().unwrap_or_default();

    let body = data["body"]
        .as_str()
        .or_else(|| data["content"].as_str())
        .unwrap_or("")
        .to_string();

    let mut adr = Adr::new(id, title);
    adr.frontmatter.status = status;
    adr.body = body;

    // Import tags if present
    if let Some(tags) = data["tags"].as_array() {
        adr.frontmatter.tags = tags
            .iter()
            .filter_map(|v| v.as_str().map(String::from))
            .collect();
    }

    Ok(adr)
}

/// Import from adr-tools format (numbered markdown files).
fn import_adr_tools(
    path: &Path,
    content: &str,
    config: &crate::core::AdrConfig,
    notes: &NotesManager,
) -> Result<Adr> {
    let filename = path
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("unknown");

    // Parse number and title from filename (e.g., "0001-use-postgresql")
    let parts: Vec<&str> = filename.splitn(2, '-').collect();
    let number: u32 = parts.first().unwrap_or(&"1").parse().unwrap_or(1);

    let id = notes.format_id(number);

    // Extract title from filename or first heading
    let title = if parts.len() > 1 {
        parts[1].replace('-', " ")
    } else {
        extract_title_from_content(content).unwrap_or_else(|| "Untitled".to_string())
    };

    // Parse status from content
    let status_str = extract_status_from_content(content).unwrap_or_else(|| "proposed".to_string());
    let status: AdrStatus = status_str.parse().unwrap_or_default();

    let mut adr = Adr::new(id, title);
    adr.frontmatter.status = status;
    adr.body = content.to_string();
    adr.frontmatter.format = Some(config.format.clone());

    Ok(adr)
}

/// Import from markdown with YAML frontmatter.
fn import_markdown(
    content: &str,
    config: &crate::core::AdrConfig,
    notes: &NotesManager,
) -> Result<Adr> {
    // Try to parse as full ADR with frontmatter
    if let Ok(adr) = Adr::from_markdown("temp".to_string(), String::new(), content) {
        // Generate new ID if needed
        let id = if adr.id == "temp" || adr.id.is_empty() {
            let next_num = notes.next_number()?;
            notes.format_id(next_num)
        } else {
            adr.id
        };

        return Ok(Adr {
            id,
            ..adr
        });
    }

    // Fall back to simple markdown parsing
    let title = extract_title_from_content(content)
        .ok_or_else(|| anyhow::anyhow!("Could not determine ADR title"))?;

    let next_num = notes.next_number()?;
    let id = notes.format_id(next_num);

    let mut adr = Adr::new(id, title);
    adr.body = content.to_string();
    adr.frontmatter.format = Some(config.format.clone());

    Ok(adr)
}

/// Extract title from markdown content.
fn extract_title_from_content(content: &str) -> Option<String> {
    for line in content.lines() {
        let trimmed = line.trim();
        if let Some(title) = trimmed.strip_prefix("# ") {
            return Some(title.trim().to_string());
        }
    }
    None
}

/// Extract status from markdown content.
fn extract_status_from_content(content: &str) -> Option<String> {
    let content_lower = content.to_lowercase();

    // Look for "## Status" section
    if let Some(idx) = content_lower.find("## status") {
        let after = &content[idx..];
        for line in after.lines().skip(1) {
            let trimmed = line.trim().to_lowercase();
            if trimmed.is_empty() {
                continue;
            }
            // Common statuses
            for status in &["accepted", "proposed", "deprecated", "superseded", "rejected", "draft"] {
                if trimmed.contains(status) {
                    return Some((*status).to_string());
                }
            }
            break;
        }
    }

    None
}
