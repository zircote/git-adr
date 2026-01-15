//! Convert ADR between formats.

use anyhow::Result;
use clap::Args as ClapArgs;
use colored::Colorize;

use crate::core::{ConfigManager, Git, NotesManager, TemplateEngine};

/// Arguments for the convert command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// ADR ID to convert.
    pub adr_id: String,

    /// Target format (nygard, madr, y-statement, alexandrian).
    #[arg(long, short)]
    pub to: String,

    /// Save in place (update the ADR).
    #[arg(long)]
    pub in_place: bool,
}

/// Supported formats.
const FORMATS: &[&str] = &["nygard", "madr", "y-statement", "alexandrian"];

/// Run the convert command.
///
/// # Errors
///
/// Returns an error if conversion fails.
pub fn run(args: Args) -> Result<()> {
    let git = Git::new();
    git.check_repository()?;

    let config = ConfigManager::new(git.clone()).load()?;
    let notes = NotesManager::new(git, config);

    // Validate target format
    if !FORMATS.contains(&args.to.as_str()) {
        anyhow::bail!(
            "Unknown format: {}. Supported formats: {}",
            args.to,
            FORMATS.join(", ")
        );
    }

    // Find the ADR
    let adrs = notes.list()?;
    let mut adr = adrs
        .into_iter()
        .find(|a| a.id == args.adr_id || a.id.contains(&args.adr_id))
        .ok_or_else(|| anyhow::anyhow!("ADR not found: {}", args.adr_id))?;

    let current_format = adr.frontmatter.format.as_deref().unwrap_or("nygard");

    if current_format == args.to {
        eprintln!(
            "{} ADR is already in {} format",
            "!".yellow(),
            args.to.cyan()
        );
        return Ok(());
    }

    eprintln!(
        "{} Converting ADR {} from {} to {}",
        "→".blue(),
        adr.id.cyan(),
        current_format.yellow(),
        args.to.green()
    );

    // Re-render the body with the new template
    let template_engine = TemplateEngine::new();
    let mut context = std::collections::HashMap::new();
    context.insert("title".to_string(), adr.frontmatter.title.clone());
    context.insert("status".to_string(), adr.frontmatter.status.to_string());
    let new_body = template_engine.render(&args.to, &context)?;

    // Update format metadata
    adr.frontmatter.format = Some(args.to.clone());
    adr.body = new_body;

    if args.in_place {
        // Save the converted ADR
        notes.update(&adr)?;
        eprintln!("{} ADR {} converted and saved", "✓".green(), adr.id.cyan());
    } else {
        // Just print the converted content
        println!("{}", adr.to_markdown()?);
        eprintln!();
        eprintln!("{} Use {} to save changes", "→".blue(), "--in-place".cyan());
    }

    Ok(())
}
