//! Integration tests for the `git-adr artifacts` command.

#![allow(deprecated)]

use assert_cmd::Command;
use predicates::prelude::*;
use std::process::Command as StdCommand;
use tempfile::TempDir;

/// Create a temporary git repository with an ADR and attachment.
fn setup_test_repo_with_artifact() -> TempDir {
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

    // Attach a file
    std::fs::write(path.join("attachment.txt"), "Attached content")
        .expect("Failed to write attachment");

    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args([
            "attach",
            "ADR-0001",
            "attachment.txt",
            "--description",
            "Test attachment",
        ])
        .assert()
        .success();

    temp_dir
}

#[test]
fn test_artifacts_list() {
    let temp_dir = setup_test_repo_with_artifact();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["artifacts", "ADR-0001"])
        .assert()
        .success()
        .stdout(predicate::str::contains("attachment.txt"));
}

#[test]
fn test_artifacts_json_format() {
    let temp_dir = setup_test_repo_with_artifact();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["artifacts", "ADR-0001", "--format", "json"])
        .assert()
        .success()
        .stdout(predicate::str::contains(r#""filename": "attachment.txt""#));
}

#[test]
fn test_artifacts_extract() {
    let temp_dir = setup_test_repo_with_artifact();
    let path = temp_dir.path();

    // Remove the original attachment file
    std::fs::remove_file(path.join("attachment.txt")).expect("Failed to remove file");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["artifacts", "ADR-0001", "--extract", "extracted.txt"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Extracted"));

    // Verify the file was extracted
    let content = std::fs::read_to_string(path.join("extracted.txt")).expect("Failed to read");
    assert_eq!(content, "Attached content");
}

#[test]
fn test_artifacts_no_artifacts() {
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

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["artifacts", "ADR-0001"])
        .assert()
        .success()
        .stderr(predicate::str::contains("No artifacts found"));
}
