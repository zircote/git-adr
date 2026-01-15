//! Create a new ADR.

use anyhow::Result;
use chrono::Utc;
use clap::Args as ClapArgs;
use colored::Colorize;

use crate::core::{Adr, AdrStatus, ConfigManager, FlexibleDate, Git, NotesManager, TemplateEngine};

/// Arguments for the new command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// ADR title.
    pub title: String,

    /// Initial status.
    #[arg(long, short, default_value = "proposed")]
    pub status: String,

    /// Tags (can be specified multiple times).
    #[arg(long, short = 'g')]
    pub tag: Vec<String>,

    /// Deciders (can be specified multiple times).
    #[arg(long, short)]
    pub deciders: Vec<String>,

    /// Link to commit SHA.
    #[arg(long, short)]
    pub link: Option<String>,

    /// Template format to use.
    #[arg(long)]
    pub template: Option<String>,

    /// Read content from file.
    #[arg(long, short)]
    pub file: Option<String>,

    /// Don't open editor.
    #[arg(long)]
    pub no_edit: bool,

    /// Preview without saving.
    #[arg(long)]
    pub preview: bool,
}

/// Run the new command.
///
/// # Errors
///
/// Returns an error if ADR creation fails.
pub fn run(args: Args) -> Result<()> {
    let git = Git::new();
    git.check_repository()?;

    let config = ConfigManager::new(git.clone()).load()?;

    if !config.initialized {
        anyhow::bail!("git-adr not initialized. Run 'git adr init' first.");
    }

    let notes = NotesManager::new(git.clone(), config.clone());

    // Generate ADR ID
    let next_num = notes.next_number()?;
    let adr_id = notes.format_id(next_num);

    eprintln!("{} Creating new ADR: {}", "→".blue(), adr_id);

    // Parse status
    let status: AdrStatus = args.status.parse().map_err(|e| anyhow::anyhow!("{}", e))?;

    // Determine template format
    let format = args.template.as_deref().unwrap_or(&config.format);

    // Get commit to attach to
    let commit = match &args.link {
        Some(sha) => sha.clone(),
        None => git.head()?,
    };

    // Create ADR struct
    let mut adr = Adr::new(adr_id.clone(), args.title.clone());
    adr.commit = commit;
    adr.frontmatter.status = status;
    adr.frontmatter.tags.clone_from(&args.tag);
    adr.frontmatter.deciders.clone_from(&args.deciders);
    adr.frontmatter.date = Some(FlexibleDate(Utc::now()));
    adr.frontmatter.format = Some(format.to_string());

    // Render template for body
    let template_engine = TemplateEngine::new();
    let mut context = std::collections::HashMap::new();
    context.insert("title".to_string(), adr.frontmatter.title.clone());
    context.insert("status".to_string(), adr.frontmatter.status.to_string());
    let body = template_engine.render(format, &context)?;
    adr.body = body;

    // Read content from file if provided
    if let Some(file_path) = &args.file {
        let file_content = std::fs::read_to_string(file_path)?;
        // If file has frontmatter, parse it; otherwise use as body
        if file_content.trim().starts_with("---") {
            let parsed = Adr::from_markdown(adr_id.clone(), adr.commit.clone(), &file_content)?;
            adr.frontmatter = parsed.frontmatter;
            adr.body = parsed.body;
        } else {
            adr.body = file_content;
        }
    }

    // Preview mode
    if args.preview {
        eprintln!("{} Preview mode - not saving", "!".yellow());
        println!("{}", adr.to_markdown()?);
        return Ok(());
    }

    // Save ADR
    notes.create(&adr)?;

    eprintln!("{} Created ADR: {}", "✓".green(), adr_id);
    eprintln!("  Title: {}", args.title);
    eprintln!("  Status: {}", adr.frontmatter.status);
    if !args.tag.is_empty() {
        eprintln!("  Tags: {}", args.tag.join(", "));
    }

    Ok(())
}
