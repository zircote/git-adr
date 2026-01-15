//! Generate project templates with ADR integration.

use anyhow::Result;
use clap::{Args as ClapArgs, Subcommand};
use colored::Colorize;
use std::fs;
use std::path::Path;

use crate::core::Git;

/// Arguments for the templates command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// Templates subcommand.
    #[command(subcommand)]
    pub command: TemplatesCommand,
}

/// Templates subcommands.
#[derive(Subcommand, Debug)]
pub enum TemplatesCommand {
    /// Generate a pull request template with ADR section.
    Pr(PrArgs),

    /// Generate GitHub issue templates for ADR workflows.
    Issue(IssueArgs),

    /// Generate or update CODEOWNERS file.
    Codeowners(CodeownersArgs),

    /// Generate all templates at once.
    All(AllArgs),
}

/// Arguments for PR template generation.
#[derive(ClapArgs, Debug)]
pub struct PrArgs {
    /// Output file path.
    #[arg(long, short, default_value = ".github/PULL_REQUEST_TEMPLATE.md")]
    pub output: String,

    /// Force overwrite existing file.
    #[arg(long, short)]
    pub force: bool,
}

/// Arguments for issue template generation.
#[derive(ClapArgs, Debug)]
pub struct IssueArgs {
    /// Output directory.
    #[arg(long, short, default_value = ".github/ISSUE_TEMPLATE")]
    pub output: String,

    /// Force overwrite existing files.
    #[arg(long, short)]
    pub force: bool,
}

/// Arguments for CODEOWNERS generation.
#[derive(ClapArgs, Debug)]
pub struct CodeownersArgs {
    /// Output file path.
    #[arg(long, short, default_value = ".github/CODEOWNERS")]
    pub output: String,

    /// ADR owner (GitHub username or team).
    #[arg(long, default_value = "@architecture-team")]
    pub owner: String,

    /// Force overwrite existing file.
    #[arg(long, short)]
    pub force: bool,
}

/// Arguments for generating all templates.
#[derive(ClapArgs, Debug)]
pub struct AllArgs {
    /// Force overwrite existing files.
    #[arg(long, short)]
    pub force: bool,
}

/// Run the templates command.
///
/// # Errors
///
/// Returns an error if template generation fails.
pub fn run(args: Args) -> Result<()> {
    let git = Git::new();
    git.check_repository()?;

    match args.command {
        TemplatesCommand::Pr(pr_args) => run_pr(pr_args),
        TemplatesCommand::Issue(issue_args) => run_issue(issue_args),
        TemplatesCommand::Codeowners(codeowners_args) => run_codeowners(codeowners_args),
        TemplatesCommand::All(all_args) => run_all(all_args),
    }
}

/// Generate PR template.
fn run_pr(args: PrArgs) -> Result<()> {
    let output_path = Path::new(&args.output);

    // Create parent directories if needed
    if let Some(parent) = output_path.parent() {
        if !parent.exists() {
            fs::create_dir_all(parent)?;
        }
    }

    if output_path.exists() && !args.force {
        anyhow::bail!(
            "PR template already exists: {}. Use --force to overwrite.",
            output_path.display()
        );
    }

    fs::write(output_path, PR_TEMPLATE)?;

    eprintln!(
        "{} Generated PR template: {}",
        "✓".green(),
        output_path.display().to_string().cyan()
    );

    Ok(())
}

/// Generate issue templates.
fn run_issue(args: IssueArgs) -> Result<()> {
    let output_dir = Path::new(&args.output);

    if !output_dir.exists() {
        fs::create_dir_all(output_dir)?;
    }

    let templates = [
        ("adr-proposal.md", ADR_PROPOSAL_TEMPLATE),
        ("adr-amendment.md", ADR_AMENDMENT_TEMPLATE),
        ("config.yml", ISSUE_CONFIG),
    ];

    eprintln!("{} Generating issue templates...", "→".blue());

    for (filename, content) in &templates {
        let file_path = output_dir.join(filename);

        if file_path.exists() && !args.force {
            eprintln!(
                "  {} {} already exists (use --force to overwrite)",
                "!".yellow(),
                filename
            );
            continue;
        }

        fs::write(&file_path, *content)?;
        eprintln!("  {} Generated {}", "✓".green(), filename.cyan());
    }

    Ok(())
}

/// Generate CODEOWNERS file.
fn run_codeowners(args: CodeownersArgs) -> Result<()> {
    let output_path = Path::new(&args.output);

    // Create parent directories if needed
    if let Some(parent) = output_path.parent() {
        if !parent.exists() {
            fs::create_dir_all(parent)?;
        }
    }

    if output_path.exists() && !args.force {
        anyhow::bail!(
            "CODEOWNERS already exists: {}. Use --force to overwrite.",
            output_path.display()
        );
    }

    let content = CODEOWNERS_TEMPLATE.replace("{owner}", &args.owner);
    fs::write(output_path, content)?;

    eprintln!(
        "{} Generated CODEOWNERS: {}",
        "✓".green(),
        output_path.display().to_string().cyan()
    );
    eprintln!("  ADR owner set to: {}", args.owner.cyan());

    Ok(())
}

/// Generate all templates.
fn run_all(args: AllArgs) -> Result<()> {
    eprintln!("{} Generating all ADR-related templates...", "→".blue());
    eprintln!();

    // Generate PR template
    run_pr(PrArgs {
        output: ".github/PULL_REQUEST_TEMPLATE.md".to_string(),
        force: args.force,
    })?;

    // Generate issue templates
    run_issue(IssueArgs {
        output: ".github/ISSUE_TEMPLATE".to_string(),
        force: args.force,
    })?;

    // Generate CODEOWNERS
    run_codeowners(CodeownersArgs {
        output: ".github/CODEOWNERS".to_string(),
        owner: "@architecture-team".to_string(),
        force: args.force,
    })?;

    eprintln!();
    eprintln!("{} All templates generated!", "✓".green());

    Ok(())
}

/// PR template content.
const PR_TEMPLATE: &str = r#"## Description

<!-- Brief description of the changes -->

## Related ADRs

<!-- Reference any related Architecture Decision Records -->
<!-- Example: Implements ADR-0005: Use PostgreSQL for primary database -->

- [ ] This PR implements/relates to an ADR
- ADR Reference: <!-- ADR-XXXX -->

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Architecture change (requires ADR)

## Checklist

- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes

## Architecture Decision

<!-- If this PR involves a significant architectural decision, please ensure an ADR exists -->

- [ ] No architectural decision needed
- [ ] ADR already exists: <!-- ADR-XXXX -->
- [ ] ADR needs to be created (link to issue: <!-- #XXX -->)
"#;

/// ADR proposal issue template.
const ADR_PROPOSAL_TEMPLATE: &str = r#"---
name: ADR Proposal
about: Propose a new Architecture Decision Record
title: "[ADR] "
labels: adr, proposal
assignees: ''
---

## Context

<!-- What is the issue that we're seeing that is motivating this decision or change? -->

## Decision Drivers

<!-- What factors are influencing this decision? -->

-
-
-

## Considered Options

<!-- What options have you considered? -->

1.
2.
3.

## Proposed Decision

<!-- What is your proposed decision? -->

## Consequences

### Positive

-

### Negative

-

### Neutral

-

## Additional Context

<!-- Add any other context, diagrams, or screenshots about the decision here -->
"#;

/// ADR amendment issue template.
const ADR_AMENDMENT_TEMPLATE: &str = r#"---
name: ADR Amendment
about: Request changes to an existing ADR
title: "[ADR Amendment] "
labels: adr, amendment
assignees: ''
---

## ADR Reference

<!-- Which ADR are you proposing to amend? -->
ADR ID:

## Reason for Amendment

<!-- Why does this ADR need to be updated? -->

- [ ] Circumstances have changed
- [ ] New information available
- [ ] Implementation revealed issues
- [ ] Other:

## Proposed Changes

<!-- What changes are you proposing? -->

## Impact Assessment

<!-- What is the impact of this change? -->

### Affected Components

-

### Migration Required

- [ ] Yes
- [ ] No

### Timeline

<!-- When should this change take effect? -->
"#;

/// Issue template config.
const ISSUE_CONFIG: &str = r#"blank_issues_enabled: true
contact_links:
  - name: ADR Documentation
    url: https://adr.github.io/
    about: Learn more about Architecture Decision Records
"#;

/// CODEOWNERS template.
const CODEOWNERS_TEMPLATE: &str = r#"# CODEOWNERS for Architecture Decision Records
# Generated by git-adr

# ADR-related files require architecture team review
# Note: git-adr stores ADRs in git notes, not files
# This covers any exported ADRs or ADR-related documentation

# ADR documentation
/docs/adr/ {owner}
/docs/architecture/ {owner}

# Exported ADRs
/adrs/ {owner}

# GitHub ADR templates
/.github/ISSUE_TEMPLATE/adr-*.md {owner}

# Architecture-related configs
/ARCHITECTURE.md {owner}
"#;
