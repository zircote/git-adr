//! Integration tests for the `git-adr link` command.

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

    // Create an additional commit to link to
    std::fs::write(path.join("file1.txt"), "content1").expect("Failed to write file");
    StdCommand::new("git")
        .args(["add", "."])
        .current_dir(path)
        .output()
        .expect("Failed to stage");
    StdCommand::new("git")
        .args(["commit", "-m", "Second commit"])
        .current_dir(path)
        .output()
        .expect("Failed to commit");

    temp_dir
}

#[test]
fn test_link_to_different_commit() {
    let temp_dir = setup_test_repo_with_adr();
    let path = temp_dir.path();

    // Get the latest commit hash
    let output = StdCommand::new("git")
        .args(["rev-parse", "HEAD"])
        .current_dir(path)
        .output()
        .expect("Failed to get HEAD");
    let commit = String::from_utf8_lossy(&output.stdout).trim().to_string();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["link", "ADR-0001", &commit])
        .assert()
        .success()
        .stderr(predicate::str::contains("Linking ADR"))
        .stderr(predicate::str::contains("moved from"));
}

#[test]
fn test_link_not_found() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["link", "ADR-9999", "HEAD"])
        .assert()
        .failure()
        .stderr(predicate::str::contains("ADR not found"));
}

#[test]
fn test_link_already_linked() {
    let temp_dir = setup_test_repo_with_adr();
    let path = temp_dir.path();

    // Get the original commit (parent of HEAD)
    let output = StdCommand::new("git")
        .args(["rev-parse", "HEAD~1"])
        .current_dir(path)
        .output()
        .expect("Failed to get HEAD~1");
    let commit = String::from_utf8_lossy(&output.stdout).trim().to_string();

    // Try to link to the same commit it's already on
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["link", "ADR-0001", &commit])
        .assert()
        .success()
        .stderr(predicate::str::contains("already linked"));
}
