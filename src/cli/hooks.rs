//! Git hooks management for ADR workflows.

use anyhow::Result;
use clap::{Args as ClapArgs, Subcommand};
use colored::Colorize;
use std::fs;
use std::os::unix::fs::PermissionsExt;
use std::path::Path;

use crate::core::Git;

/// Arguments for the hooks command.
#[derive(ClapArgs, Debug)]
pub struct Args {
    /// Hooks subcommand.
    #[command(subcommand)]
    pub command: HooksCommand,
}

/// Hooks subcommands.
#[derive(Subcommand, Debug)]
pub enum HooksCommand {
    /// Install ADR git hooks.
    Install(InstallArgs),

    /// Uninstall ADR git hooks.
    Uninstall(UninstallArgs),

    /// Show hook installation status.
    Status,
}

/// Arguments for hooks install.
#[derive(ClapArgs, Debug)]
pub struct InstallArgs {
    /// Force overwrite existing hooks.
    #[arg(long, short)]
    pub force: bool,

    /// Install pre-push hook for ADR validation.
    #[arg(long, default_value = "true")]
    pub pre_push: bool,

    /// Install post-merge hook for ADR sync.
    #[arg(long)]
    pub post_merge: bool,
}

/// Arguments for hooks uninstall.
#[derive(ClapArgs, Debug)]
pub struct UninstallArgs {
    /// Remove all ADR hooks.
    #[arg(long)]
    pub all: bool,
}

/// Run the hooks command.
///
/// # Errors
///
/// Returns an error if hook operations fail.
pub fn run(args: Args) -> Result<()> {
    let git = Git::new();
    git.check_repository()?;

    match args.command {
        HooksCommand::Install(install_args) => run_install(install_args, &git),
        HooksCommand::Uninstall(uninstall_args) => run_uninstall(uninstall_args, &git),
        HooksCommand::Status => run_status(&git),
    }
}

/// Install git hooks.
fn run_install(args: InstallArgs, git: &Git) -> Result<()> {
    let hooks_dir = git.repo_root()?.join(".git/hooks");

    if !hooks_dir.exists() {
        fs::create_dir_all(&hooks_dir)?;
    }

    eprintln!("{} Installing ADR git hooks...", "→".blue());
    let mut installed = 0;

    if args.pre_push {
        let hook_path = hooks_dir.join("pre-push");
        if install_hook(&hook_path, PRE_PUSH_HOOK, args.force)? {
            eprintln!("  {} Installed pre-push hook", "✓".green());
            installed += 1;
        }
    }

    if args.post_merge {
        let hook_path = hooks_dir.join("post-merge");
        if install_hook(&hook_path, POST_MERGE_HOOK, args.force)? {
            eprintln!("  {} Installed post-merge hook", "✓".green());
            installed += 1;
        }
    }

    if installed == 0 {
        eprintln!(
            "{} No hooks were installed. Use --force to overwrite existing hooks.",
            "!".yellow()
        );
    } else {
        eprintln!();
        eprintln!(
            "{} Installed {} hook(s)",
            "✓".green(),
            installed.to_string().cyan()
        );
    }

    Ok(())
}

/// Uninstall git hooks.
fn run_uninstall(args: UninstallArgs, git: &Git) -> Result<()> {
    let hooks_dir = git.repo_root()?.join(".git/hooks");

    let hooks_to_remove = if args.all {
        vec!["pre-push", "post-merge"]
    } else {
        vec!["pre-push"]
    };

    eprintln!("{} Uninstalling ADR git hooks...", "→".blue());
    let mut removed = 0;

    for hook_name in hooks_to_remove {
        let hook_path = hooks_dir.join(hook_name);
        if hook_path.exists() && is_adr_hook(&hook_path)? {
            fs::remove_file(&hook_path)?;
            eprintln!("  {} Removed {} hook", "✓".green(), hook_name);
            removed += 1;
        }
    }

    if removed == 0 {
        eprintln!("{} No ADR hooks found to remove", "→".yellow());
    } else {
        eprintln!();
        eprintln!(
            "{} Removed {} hook(s)",
            "✓".green(),
            removed.to_string().cyan()
        );
    }

    Ok(())
}

/// Show hook status.
fn run_status(git: &Git) -> Result<()> {
    let hooks_dir = git.repo_root()?.join(".git/hooks");

    eprintln!("{} ADR Hook Status:", "→".blue());
    println!();

    let hooks = [
        ("pre-push", "Validates ADR references before push"),
        ("post-merge", "Syncs ADRs after merge"),
    ];

    for (name, description) in &hooks {
        let hook_path = hooks_dir.join(name);
        let status = if hook_path.exists() {
            if is_adr_hook(&hook_path)? {
                "installed".green().to_string()
            } else {
                "exists (not ADR)".yellow().to_string()
            }
        } else {
            "not installed".dimmed().to_string()
        };

        println!("  {} {} [{}]", name.bold(), description.dimmed(), status);
    }

    Ok(())
}

/// Install a single hook.
fn install_hook(path: &Path, content: &str, force: bool) -> Result<bool> {
    if path.exists() && !force {
        if is_adr_hook(path)? {
            eprintln!(
                "  {} {} already installed (use --force to reinstall)",
                "→".yellow(),
                path.file_name().unwrap_or_default().to_string_lossy()
            );
        } else {
            eprintln!(
                "  {} {} exists but is not an ADR hook (use --force to overwrite)",
                "!".yellow(),
                path.file_name().unwrap_or_default().to_string_lossy()
            );
        }
        return Ok(false);
    }

    fs::write(path, content)?;

    // Make executable
    let mut perms = fs::metadata(path)?.permissions();
    perms.set_mode(0o755);
    fs::set_permissions(path, perms)?;

    Ok(true)
}

/// Check if a hook is an ADR hook (contains marker).
fn is_adr_hook(path: &Path) -> Result<bool> {
    let content = fs::read_to_string(path)?;
    Ok(content.contains("git-adr"))
}

/// Pre-push hook content.
const PRE_PUSH_HOOK: &str = r#"#!/bin/sh
# git-adr pre-push hook
# Validates ADR references in commits before push

# Get the remote and URL
remote="$1"
url="$2"

# Read stdin for refs being pushed
while read local_ref local_sha remote_ref remote_sha; do
    # Skip if deleting a branch
    if [ "$local_sha" = "0000000000000000000000000000000000000000" ]; then
        continue
    fi

    # Get the range of commits being pushed
    if [ "$remote_sha" = "0000000000000000000000000000000000000000" ]; then
        # New branch - check all commits
        range="$local_sha"
    else
        range="$remote_sha..$local_sha"
    fi

    # Check for ADR references in commit messages
    commits_with_adr=$(git log --format="%H %s" "$range" 2>/dev/null | grep -i "ADR-" || true)

    if [ -n "$commits_with_adr" ]; then
        echo "→ Found commits referencing ADRs:"
        echo "$commits_with_adr" | while read line; do
            echo "  $line"
        done

        # Sync ADRs to ensure they're pushed
        if command -v git-adr >/dev/null 2>&1; then
            echo "→ Syncing ADR notes..."
            git-adr sync push --quiet 2>/dev/null || true
        fi
    fi
done

exit 0
"#;

/// Post-merge hook content.
const POST_MERGE_HOOK: &str = r#"#!/bin/sh
# git-adr post-merge hook
# Syncs ADRs after merge

echo "→ Syncing ADR notes after merge..."

if command -v git-adr >/dev/null 2>&1; then
    git-adr sync pull --quiet 2>/dev/null || true
fi

exit 0
"#;
