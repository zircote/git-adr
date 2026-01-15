//! Low-level git operations.
//!
//! This module provides a wrapper around git subprocess calls,
//! handling command execution, error parsing, and output processing.

use std::path::{Path, PathBuf};
use std::process::{Command, Output};

use crate::Error;

/// Git subprocess wrapper.
#[derive(Debug, Clone)]
pub struct Git {
    /// Working directory for git commands.
    work_dir: PathBuf,
    /// Path to git executable.
    git_path: PathBuf,
}

impl Default for Git {
    fn default() -> Self {
        Self::new()
    }
}

impl Git {
    /// Create a new Git instance using the current directory.
    #[must_use]
    pub fn new() -> Self {
        Self {
            work_dir: std::env::current_dir().unwrap_or_else(|_| PathBuf::from(".")),
            git_path: PathBuf::from("git"),
        }
    }

    /// Create a new Git instance with a specific working directory.
    #[must_use]
    pub fn with_work_dir<P: AsRef<Path>>(path: P) -> Self {
        Self {
            work_dir: path.as_ref().to_path_buf(),
            git_path: PathBuf::from("git"),
        }
    }

    /// Get the working directory.
    #[must_use]
    pub fn work_dir(&self) -> &Path {
        &self.work_dir
    }

    /// Check if we're in a git repository.
    ///
    /// # Errors
    ///
    /// Returns an error if git is not found or we're not in a repository.
    pub fn check_repository(&self) -> Result<(), Error> {
        let output = self.run(&["rev-parse", "--git-dir"])?;
        if !output.status.success() {
            return Err(Error::NotARepository {
                path: Some(self.work_dir.display().to_string()),
            });
        }
        Ok(())
    }

    /// Get the repository root directory.
    ///
    /// # Errors
    ///
    /// Returns an error if not in a git repository.
    pub fn repo_root(&self) -> Result<PathBuf, Error> {
        self.check_repository()?;
        let output = self.run_output(&["rev-parse", "--show-toplevel"])?;
        Ok(PathBuf::from(output.trim()))
    }

    /// Run a git command and return the raw output.
    ///
    /// # Errors
    ///
    /// Returns an error if the command fails to execute.
    pub fn run(&self, args: &[&str]) -> Result<Output, Error> {
        Command::new(&self.git_path)
            .current_dir(&self.work_dir)
            .args(args)
            .output()
            .map_err(|e| {
                if e.kind() == std::io::ErrorKind::NotFound {
                    Error::GitNotFound
                } else {
                    Error::Git {
                        message: e.to_string(),
                        command: args.iter().map(|s| (*s).to_string()).collect(),
                        exit_code: -1,
                        stderr: String::new(),
                    }
                }
            })
    }

    /// Run a git command and return stdout as a string.
    ///
    /// # Errors
    ///
    /// Returns an error if the command fails or returns non-zero exit code.
    pub fn run_output(&self, args: &[&str]) -> Result<String, Error> {
        let output = self.run(args)?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr).to_string();
            return Err(Error::Git {
                message: format!("git command failed: git {}", args.join(" ")),
                command: args.iter().map(|s| (*s).to_string()).collect(),
                exit_code: output.status.code().unwrap_or(-1),
                stderr,
            });
        }

        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    }

    /// Run a git command silently, only checking for success.
    ///
    /// # Errors
    ///
    /// Returns an error if the command fails.
    pub fn run_silent(&self, args: &[&str]) -> Result<(), Error> {
        let output = self.run(args)?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr).to_string();
            return Err(Error::Git {
                message: format!("git command failed: git {}", args.join(" ")),
                command: args.iter().map(|s| (*s).to_string()).collect(),
                exit_code: output.status.code().unwrap_or(-1),
                stderr,
            });
        }

        Ok(())
    }

    /// Get the current HEAD commit hash.
    ///
    /// # Errors
    ///
    /// Returns an error if HEAD cannot be resolved.
    pub fn head(&self) -> Result<String, Error> {
        let output = self.run_output(&["rev-parse", "HEAD"])?;
        Ok(output.trim().to_string())
    }

    /// Get a short commit hash.
    ///
    /// # Errors
    ///
    /// Returns an error if the commit cannot be resolved.
    pub fn short_hash(&self, commit: &str) -> Result<String, Error> {
        let output = self.run_output(&["rev-parse", "--short", commit])?;
        Ok(output.trim().to_string())
    }

    /// Get a git config value.
    ///
    /// # Errors
    ///
    /// Returns an error if the config key doesn't exist.
    pub fn config_get(&self, key: &str) -> Result<Option<String>, Error> {
        let output = self.run(&["config", "--get", key])?;

        if output.status.success() {
            Ok(Some(
                String::from_utf8_lossy(&output.stdout).trim().to_string(),
            ))
        } else {
            Ok(None)
        }
    }

    /// Set a git config value.
    ///
    /// # Errors
    ///
    /// Returns an error if the config cannot be set.
    pub fn config_set(&self, key: &str, value: &str) -> Result<(), Error> {
        self.run_silent(&["config", key, value])
    }

    /// Unset a git config value.
    ///
    /// If `all` is true, removes all values for multi-valued keys.
    ///
    /// # Errors
    ///
    /// Returns an error if the config cannot be unset.
    pub fn config_unset(&self, key: &str, all: bool) -> Result<(), Error> {
        let args: Vec<&str> = if all {
            vec!["config", "--unset-all", key]
        } else {
            vec!["config", "--unset", key]
        };

        // Ignore error if the key doesn't exist (exit code 5)
        let output = self.run(&args)?;
        if output.status.success() || output.status.code() == Some(5) {
            Ok(())
        } else {
            Err(Error::Git {
                message: format!(
                    "Failed to unset config {key}: {}",
                    String::from_utf8_lossy(&output.stderr)
                ),
                command: args.iter().map(|s| (*s).to_string()).collect(),
                exit_code: output.status.code().unwrap_or(-1),
                stderr: String::from_utf8_lossy(&output.stderr).to_string(),
            })
        }
    }

    /// Get notes content for a commit.
    ///
    /// # Errors
    ///
    /// Returns an error if the notes cannot be read.
    pub fn notes_show(&self, notes_ref: &str, commit: &str) -> Result<Option<String>, Error> {
        let output = self.run(&["notes", "--ref", notes_ref, "show", commit])?;

        if output.status.success() {
            Ok(Some(String::from_utf8_lossy(&output.stdout).to_string()))
        } else {
            Ok(None)
        }
    }

    /// Add or update notes for a commit.
    ///
    /// # Errors
    ///
    /// Returns an error if the notes cannot be added.
    pub fn notes_add(&self, notes_ref: &str, commit: &str, content: &str) -> Result<(), Error> {
        self.run_silent(&[
            "notes", "--ref", notes_ref, "add", "-f", "-m", content, commit,
        ])
    }

    /// Remove notes for a commit.
    ///
    /// # Errors
    ///
    /// Returns an error if the notes cannot be removed.
    pub fn notes_remove(&self, notes_ref: &str, commit: &str) -> Result<(), Error> {
        self.run_silent(&["notes", "--ref", notes_ref, "remove", commit])
    }

    /// List all notes in a ref.
    ///
    /// # Errors
    ///
    /// Returns an error if notes cannot be listed.
    pub fn notes_list(&self, notes_ref: &str) -> Result<Vec<(String, String)>, Error> {
        let output = self.run(&["notes", "--ref", notes_ref, "list"])?;

        if !output.status.success() {
            // No notes ref yet is not an error
            return Ok(Vec::new());
        }

        let stdout = String::from_utf8_lossy(&output.stdout);
        let mut results = Vec::new();

        for line in stdout.lines() {
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() >= 2 {
                results.push((parts[0].to_string(), parts[1].to_string()));
            }
        }

        Ok(results)
    }

    /// Push notes to a remote.
    ///
    /// # Errors
    ///
    /// Returns an error if push fails.
    pub fn notes_push(&self, remote: &str, notes_ref: &str) -> Result<(), Error> {
        self.run_silent(&[
            "push",
            remote,
            &format!("refs/notes/{notes_ref}:refs/notes/{notes_ref}"),
        ])
    }

    /// Fetch notes from a remote.
    ///
    /// # Errors
    ///
    /// Returns an error if fetch fails.
    pub fn notes_fetch(&self, remote: &str, notes_ref: &str) -> Result<(), Error> {
        self.run_silent(&[
            "fetch",
            remote,
            &format!("refs/notes/{notes_ref}:refs/notes/{notes_ref}"),
        ])
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_git_new() {
        let git = Git::new();
        assert!(git.work_dir().exists() || git.work_dir() == Path::new("."));
    }

    #[test]
    fn test_git_default() {
        let git = Git::default();
        assert!(git.work_dir().exists() || git.work_dir() == Path::new("."));
    }

    #[test]
    fn test_git_with_work_dir() {
        let temp_dir = TempDir::new().unwrap();
        let git = Git::with_work_dir(temp_dir.path());
        assert_eq!(git.work_dir(), temp_dir.path());
    }

    #[test]
    fn test_git_work_dir() {
        let git = Git::new();
        let _ = git.work_dir();
    }

    #[test]
    fn test_check_repository_not_a_repo() {
        let temp_dir = TempDir::new().unwrap();
        let git = Git::with_work_dir(temp_dir.path());
        let result = git.check_repository();
        assert!(result.is_err());
    }

    #[test]
    fn test_run_success() {
        let git = Git::new();
        let output = git.run(&["--version"]).expect("git --version should work");
        assert!(output.status.success());
    }

    #[test]
    fn test_run_output_success() {
        let git = Git::new();
        let output = git
            .run_output(&["--version"])
            .expect("git --version should work");
        assert!(output.contains("git version"));
    }

    #[test]
    fn test_run_output_failure() {
        let temp_dir = TempDir::new().unwrap();
        let git = Git::with_work_dir(temp_dir.path());
        // rev-parse HEAD fails outside a git repo
        let result = git.run_output(&["rev-parse", "HEAD"]);
        assert!(result.is_err());
    }

    #[test]
    fn test_run_silent_failure() {
        let temp_dir = TempDir::new().unwrap();
        let git = Git::with_work_dir(temp_dir.path());
        // This will fail because we're not in a git repo
        let result = git.run_silent(&["status"]);
        assert!(result.is_err());
    }

    #[test]
    fn test_notes_list_empty() {
        let temp_dir = TempDir::new().unwrap();
        let git = Git::with_work_dir(temp_dir.path());
        // Initialize git repo but no notes
        Command::new("git")
            .current_dir(temp_dir.path())
            .args(["init"])
            .output()
            .unwrap();
        let result = git.notes_list("adr");
        assert!(result.is_ok());
        assert!(result.unwrap().is_empty());
    }

    #[test]
    fn test_config_get_nonexistent() {
        let temp_dir = TempDir::new().unwrap();
        Command::new("git")
            .current_dir(temp_dir.path())
            .args(["init"])
            .output()
            .unwrap();
        let git = Git::with_work_dir(temp_dir.path());
        let result = git.config_get("nonexistent.key");
        assert!(result.is_ok());
        assert!(result.unwrap().is_none());
    }

    #[test]
    fn test_config_set_and_get() {
        let temp_dir = TempDir::new().unwrap();
        Command::new("git")
            .current_dir(temp_dir.path())
            .args(["init"])
            .output()
            .unwrap();
        let git = Git::with_work_dir(temp_dir.path());
        git.config_set("test.key", "test_value").unwrap();
        let result = git.config_get("test.key").unwrap();
        assert_eq!(result, Some("test_value".to_string()));
    }

    #[test]
    fn test_config_unset() {
        let temp_dir = TempDir::new().unwrap();
        Command::new("git")
            .current_dir(temp_dir.path())
            .args(["init"])
            .output()
            .unwrap();
        let git = Git::with_work_dir(temp_dir.path());
        git.config_set("test.key", "value").unwrap();
        git.config_unset("test.key", false).unwrap();
        let result = git.config_get("test.key").unwrap();
        assert!(result.is_none());
    }

    #[test]
    fn test_config_unset_nonexistent() {
        let temp_dir = TempDir::new().unwrap();
        Command::new("git")
            .current_dir(temp_dir.path())
            .args(["init"])
            .output()
            .unwrap();
        let git = Git::with_work_dir(temp_dir.path());
        // Unsetting a key that doesn't exist should not error (exit code 5)
        let result = git.config_unset("nonexistent.key", false);
        assert!(result.is_ok());
    }

    #[test]
    fn test_notes_show_nonexistent() {
        let temp_dir = TempDir::new().unwrap();
        Command::new("git")
            .current_dir(temp_dir.path())
            .args(["init"])
            .output()
            .unwrap();
        // Create initial commit
        std::fs::write(temp_dir.path().join("file.txt"), "content").unwrap();
        Command::new("git")
            .current_dir(temp_dir.path())
            .args(["add", "."])
            .output()
            .unwrap();
        Command::new("git")
            .current_dir(temp_dir.path())
            .args(["config", "user.email", "test@example.com"])
            .output()
            .unwrap();
        Command::new("git")
            .current_dir(temp_dir.path())
            .args(["config", "user.name", "Test"])
            .output()
            .unwrap();
        Command::new("git")
            .current_dir(temp_dir.path())
            .args(["commit", "-m", "Initial"])
            .output()
            .unwrap();

        let git = Git::with_work_dir(temp_dir.path());
        let result = git.notes_show("adr", "HEAD");
        assert!(result.is_ok());
        assert!(result.unwrap().is_none());
    }

    #[test]
    fn test_repo_root() {
        let temp_dir = TempDir::new().unwrap();
        Command::new("git")
            .current_dir(temp_dir.path())
            .args(["init"])
            .output()
            .unwrap();
        let git = Git::with_work_dir(temp_dir.path());
        let root = git.repo_root();
        assert!(root.is_ok());
    }

    #[test]
    fn test_head_and_short_hash() {
        let temp_dir = TempDir::new().unwrap();
        Command::new("git")
            .current_dir(temp_dir.path())
            .args(["init"])
            .output()
            .unwrap();
        std::fs::write(temp_dir.path().join("file.txt"), "content").unwrap();
        Command::new("git")
            .current_dir(temp_dir.path())
            .args(["add", "."])
            .output()
            .unwrap();
        Command::new("git")
            .current_dir(temp_dir.path())
            .args(["config", "user.email", "test@example.com"])
            .output()
            .unwrap();
        Command::new("git")
            .current_dir(temp_dir.path())
            .args(["config", "user.name", "Test"])
            .output()
            .unwrap();
        Command::new("git")
            .current_dir(temp_dir.path())
            .args(["commit", "-m", "Initial"])
            .output()
            .unwrap();

        let git = Git::with_work_dir(temp_dir.path());
        let head = git.head().unwrap();
        assert_eq!(head.len(), 40); // Full SHA

        let short = git.short_hash(&head).unwrap();
        assert!(short.len() < head.len());
    }
}
