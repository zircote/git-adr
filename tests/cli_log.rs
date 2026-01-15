//! Integration tests for the `git-adr log` command.

#![allow(deprecated)]

use assert_cmd::Command;
use predicates::prelude::*;
use std::process::Command as StdCommand;
use tempfile::TempDir;

/// Create a temporary git repository with an ADR.
fn setup_test_repo_with_adr() -> TempDir {
    let temp_dir = TempDir::new().expect("Failed to create temp directory");
    let path = temp_dir.path();

    StdCommand::new("git")
        .args(["init"])
        .current_dir(path)
        .output()
        .expect("Failed to init git repo");

    StdCommand::new("git")
        .args(["config", "user.email", "test@example.com"])
        .current_dir(path)
        .output()
        .expect("Failed to set git user email");

    StdCommand::new("git")
        .args(["config", "user.name", "Test User"])
        .current_dir(path)
        .output()
        .expect("Failed to set git user name");

    std::fs::write(path.join("README.md"), "# Test Repo\n").expect("Failed to write README");
    StdCommand::new("git")
        .args(["add", "."])
        .current_dir(path)
        .output()
        .expect("Failed to stage files");
    StdCommand::new("git")
        .args(["commit", "-m", "Initial commit"])
        .current_dir(path)
        .output()
        .expect("Failed to create initial commit");

    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .arg("init")
        .assert()
        .success();

    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["new", "Test ADR"])
        .assert()
        .success();

    // Create additional commits
    for i in 1..4 {
        std::fs::write(path.join(format!("file{i}.txt")), format!("content{i}"))
            .expect("Failed to write file");
        StdCommand::new("git")
            .args(["add", "."])
            .current_dir(path)
            .output()
            .expect("Failed to stage");
        StdCommand::new("git")
            .args(["commit", "-m", &format!("Commit {i}")])
            .current_dir(path)
            .output()
            .expect("Failed to commit");
    }

    temp_dir
}

#[test]
fn test_log_shows_commits() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .arg("log")
        .assert()
        .success()
        .stdout(predicate::str::contains("Commit"))
        .stderr(predicate::str::contains("commit(s) shown"));
}

#[test]
fn test_log_shows_linked_adrs() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .arg("log")
        .assert()
        .success()
        .stderr(predicate::str::contains("with ADRs"));
}

#[test]
fn test_log_linked_only() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["log", "--linked-only"])
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR-0001"));
}

#[test]
fn test_log_with_count() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["log", "-n", "2"])
        .assert()
        .success()
        .stderr(predicate::str::contains("2 commit(s) shown"));
}

#[test]
fn test_log_linked_only_no_matches() {
    let temp_dir = TempDir::new().expect("Failed to create temp directory");
    let path = temp_dir.path();

    StdCommand::new("git")
        .args(["init"])
        .current_dir(path)
        .output()
        .expect("Failed to init git repo");

    StdCommand::new("git")
        .args(["config", "user.email", "test@example.com"])
        .current_dir(path)
        .output()
        .expect("Failed to set git user email");

    StdCommand::new("git")
        .args(["config", "user.name", "Test User"])
        .current_dir(path)
        .output()
        .expect("Failed to set git user name");

    std::fs::write(path.join("README.md"), "# Test Repo\n").expect("Failed to write README");
    StdCommand::new("git")
        .args(["add", "."])
        .current_dir(path)
        .output()
        .expect("Failed to stage files");
    StdCommand::new("git")
        .args(["commit", "-m", "Initial commit"])
        .current_dir(path)
        .output()
        .expect("Failed to create initial commit");

    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .arg("init")
        .assert()
        .success();

    // No ADRs created, but run log with --linked-only
    // Should show "No commits found" since no commits have ADRs
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["log", "--linked-only"])
        .assert()
        .success()
        .stderr(predicate::str::contains("No commits found"));
}
