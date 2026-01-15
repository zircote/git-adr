//! Create a superseding ADR.

use anyhow::Result;
use chrono::Utc;
use clap::Args as ClapArgs;
use colored::Colorize;

use crate::core::{Adr, AdrStatus, ConfigManager, FlexibleDate, Git, NotesManager, TemplateEngine};

/// Arguments for the supersede command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// ADR ID to supersede.
    pub adr_id: String,

    /// Title for the new ADR.
    pub title: String,

    /// Template format for new ADR.
    #[arg(long)]
    pub template: Option<String>,
}

/// Run the supersede command.
///
/// # Errors
///
/// Returns an error if supersession fails.
pub fn run(args: Args) -> Result<()> {
    let git = Git::new();
    git.check_repository()?;

    let config = ConfigManager::new(git.clone()).load()?;
    let notes = NotesManager::new(git.clone(), config.clone());

    // Find the ADR to supersede
    let adrs = notes.list()?;
    let mut old_adr = adrs
        .into_iter()
        .find(|a| a.id == args.adr_id || a.id.contains(&args.adr_id))
        .ok_or_else(|| anyhow::anyhow!("ADR not found: {}", args.adr_id))?;

    eprintln!(
        "{} Superseding ADR {} with: {}",
        "→".blue(),
        old_adr.id.cyan(),
        args.title.yellow()
    );

    // Generate new ADR ID
    let next_num = notes.next_number()?;
    let new_adr_id = notes.format_id(next_num);

    // Determine template format
    let format = args.template.as_deref().unwrap_or(&config.format);

    // Create new ADR
    let mut new_adr = Adr::new(new_adr_id.clone(), args.title.clone());
    new_adr.commit = git.head()?;
    new_adr.frontmatter.status = AdrStatus::Proposed;
    new_adr.frontmatter.date = Some(FlexibleDate(Utc::now()));
    new_adr.frontmatter.format = Some(format.to_string());

    // Inherit tags from old ADR
    new_adr
        .frontmatter
        .tags
        .clone_from(&old_adr.frontmatter.tags);

    // Add supersedes link
    new_adr.frontmatter.supersedes = Some(old_adr.id.clone());

    // Render template for body
    let template_engine = TemplateEngine::new();
    let mut context = std::collections::HashMap::new();
    context.insert("title".to_string(), new_adr.frontmatter.title.clone());
    context.insert("status".to_string(), new_adr.frontmatter.status.to_string());
    let body = template_engine.render(format, &context)?;
    new_adr.body = body;

    // Save new ADR
    notes.create(&new_adr)?;

    // Update old ADR status to superseded
    old_adr.frontmatter.status = AdrStatus::Superseded;
    old_adr.frontmatter.superseded_by = Some(new_adr_id.clone());
    notes.update(&old_adr)?;

    eprintln!("{} Created new ADR: {}", "✓".green(), new_adr_id.cyan());
    eprintln!(
        "{} Updated {} status to superseded",
        "✓".green(),
        old_adr.id.cyan()
    );

    Ok(())
}
