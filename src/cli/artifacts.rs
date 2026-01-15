//! List artifacts attached to an ADR.

use anyhow::Result;
use clap::Args as ClapArgs;
use colored::Colorize;

use crate::core::{ConfigManager, Git, NotesManager, ARTIFACTS_NOTES_REF};

/// Arguments for the artifacts command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// ADR ID.
    pub adr_id: String,

    /// Output format (text, json).
    #[arg(long, short, default_value = "text")]
    pub format: String,

    /// Extract artifact to file.
    #[arg(long)]
    pub extract: Option<String>,

    /// Remove artifact from ADR.
    #[arg(long)]
    pub remove: bool,
}

/// Run the artifacts command.
///
/// # Errors
///
/// Returns an error if listing fails.
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

    // Get artifacts for this ADR's commit
    let artifact_content = git.notes_show(ARTIFACTS_NOTES_REF, &adr.commit)?;

    match artifact_content {
        Some(content) => {
            // Parse artifact JSON
            let artifact: serde_json::Value = serde_json::from_str(&content)?;

            if args.remove {
                // Remove the artifact from this ADR
                git.notes_remove(ARTIFACTS_NOTES_REF, &adr.commit)?;
                eprintln!(
                    "{} Removed artifact {} from ADR {}",
                    "✓".green(),
                    artifact["filename"].as_str().unwrap_or("unknown").cyan(),
                    adr.id.cyan()
                );
            } else if let Some(extract_name) = &args.extract {
                // Extract the artifact to a file
                use base64::{engine::general_purpose::STANDARD as BASE64, Engine};

                let encoded = artifact["content"]
                    .as_str()
                    .ok_or_else(|| anyhow::anyhow!("No content in artifact"))?;

                let decoded = BASE64.decode(encoded)?;
                std::fs::write(extract_name, decoded)?;

                eprintln!(
                    "{} Extracted {} ({} bytes)",
                    "✓".green(),
                    extract_name.cyan(),
                    artifact["size"]
                );
            } else if args.format.as_str() == "json" {
                // Remove content field for listing
                let mut listing = artifact;
                if let Some(obj) = listing.as_object_mut() {
                    obj.remove("content");
                }
                println!("{}", serde_json::to_string_pretty(&listing)?);
            } else {
                eprintln!("{} Artifacts for ADR {}:", "→".blue(), adr.id.cyan());
                println!();
                println!(
                    "  {} {}",
                    "Filename:".bold(),
                    artifact["filename"].as_str().unwrap_or("unknown").cyan()
                );
                println!(
                    "  {} {} bytes",
                    "Size:".bold(),
                    artifact["size"].as_u64().unwrap_or(0)
                );
                if let Some(desc) = artifact["description"].as_str() {
                    if !desc.is_empty() {
                        println!("  {} {}", "Description:".bold(), desc);
                    }
                }
            }
        }
        None => {
            eprintln!("{} No artifacts found for ADR {}", "→".yellow(), adr.id);
        }
    }

    Ok(())
}
