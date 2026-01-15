//! Integration tests for the `git-adr convert` command.

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

    temp_dir
}

#[test]
fn test_convert_to_nygard() {
    let temp_dir = setup_test_repo_with_adr();

    // Default format is madr, so convert to nygard
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["convert", "ADR-0001", "--to", "nygard"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Converting"))
        .stdout(predicate::str::contains("---")); // Should output markdown
}

#[test]
fn test_convert_to_y_statement() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["convert", "ADR-0001", "--to", "y-statement"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Converting"));
}

#[test]
fn test_convert_in_place() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["convert", "ADR-0001", "--to", "alexandrian", "--in-place"])
        .assert()
        .success()
        .stderr(predicate::str::contains("converted and saved"));
}

#[test]
fn test_convert_unknown_format() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["convert", "ADR-0001", "--to", "invalid-format"])
        .assert()
        .failure()
        .stderr(predicate::str::contains("Unknown format"));
}

#[test]
fn test_convert_same_format() {
    let temp_dir = setup_test_repo_with_adr();

    // ADRs are created with madr format by default
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["convert", "ADR-0001", "--to", "madr"])
        .assert()
        .success()
        .stderr(predicate::str::contains("already in"));
}

#[test]
fn test_convert_adr_not_found() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["convert", "ADR-9999", "--to", "madr"])
        .assert()
        .failure()
        .stderr(predicate::str::contains("ADR not found"));
}
