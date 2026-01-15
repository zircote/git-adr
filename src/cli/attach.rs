//! Attach a file to an ADR.

use anyhow::Result;
use base64::{engine::general_purpose::STANDARD as BASE64, Engine};
use clap::Args as ClapArgs;
use colored::Colorize;
use std::path::Path;

use crate::core::{ConfigManager, Git, NotesManager, ARTIFACTS_NOTES_REF};

/// Arguments for the attach command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// ADR ID.
    pub adr_id: String,

    /// File to attach.
    pub file: String,

    /// Override filename.
    #[arg(long)]
    pub name: Option<String>,

    /// Description/alt text for the attachment.
    #[arg(long)]
    pub description: Option<String>,
}

/// Run the attach command.
///
/// # Errors
///
/// Returns an error if attachment fails.
pub fn run(args: Args) -> Result<()> {
    let git = Git::new();
    git.check_repository()?;

    let config = ConfigManager::new(git.clone()).load()?;
    let notes = NotesManager::new(git.clone(), config);

    // Find the ADR
    let adrs = notes.list()?;
    let adr = adrs
        .into_iter()
        .find(|a| a.id == args.adr_id || a.id.contains(&args.adr_id))
        .ok_or_else(|| anyhow::anyhow!("ADR not found: {}", args.adr_id))?;

    // Check file exists
    let file_path = Path::new(&args.file);
    if !file_path.exists() {
        anyhow::bail!("File not found: {}", args.file);
    }

    // Get file name
    let filename = args.name.clone().unwrap_or_else(|| {
        file_path.file_name().map_or_else(
            || "attachment".to_string(),
            |s| s.to_string_lossy().to_string(),
        )
    });

    eprintln!(
        "{} Attaching {} to ADR {}",
        "→".blue(),
        filename.cyan(),
        adr.id.cyan()
    );

    // Read file content
    let content = std::fs::read(file_path)?;
    let encoded = BASE64.encode(&content);

    // Get file metadata
    let metadata = std::fs::metadata(file_path)?;
    let size = metadata.len();

    // Create artifact metadata
    let artifact = serde_json::json!({
        "filename": filename,
        "size": size,
        "adr_id": adr.id,
        "description": args.description,
        "content": encoded,
    });

    // Store as a note on the ADR's commit
    // Format: JSON blob with filename, size, content (base64)
    let artifact_content = serde_json::to_string_pretty(&artifact)?;

    git.notes_add(ARTIFACTS_NOTES_REF, &adr.commit, &artifact_content)?;

    eprintln!(
        "{} Attached {} ({} bytes) to ADR {}",
        "✓".green(),
        filename.cyan(),
        size,
        adr.id.cyan()
    );

    Ok(())
}
