//! Integration tests for the `git-adr show` command.

#![allow(deprecated)]

use assert_cmd::Command;
use predicates::prelude::*;
use std::process::Command as StdCommand;
use tempfile::TempDir;

/// Create a temporary git repository with an ADR.
fn setup_test_repo_with_adr() -> TempDir {
    let temp_dir = TempDir::new().expect("Failed to create temp directory");
    let path = temp_dir.path();

    // Initialize git repo
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

    // Initialize ADR
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .arg("init")
        .assert()
        .success();

    // Create an ADR
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["new", "Use PostgreSQL", "--tag", "database", "--status", "accepted"])
        .assert()
        .success();

    temp_dir
}

#[test]
fn test_show_by_full_id() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["show", "ADR-0001"])
        .assert()
        .success()
        .stdout(predicate::str::contains("Use PostgreSQL"))
        .stdout(predicate::str::contains("accepted"));
}

#[test]
fn test_show_by_partial_id() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["show", "0001"])
        .assert()
        .success()
        .stdout(predicate::str::contains("Use PostgreSQL"));
}

#[test]
fn test_show_json_format() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["show", "ADR-0001", "--format", "json"])
        .assert()
        .success()
        .stdout(predicate::str::contains(r#""id": "ADR-0001""#))
        .stdout(predicate::str::contains(r#""title": "Use PostgreSQL""#))
        .stdout(predicate::str::contains(r#""status": "accepted""#));
}

#[test]
fn test_show_yaml_format() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["show", "ADR-0001", "--format", "yaml"])
        .assert()
        .success()
        .stdout(predicate::str::contains("title: Use PostgreSQL"));
}

#[test]
fn test_show_metadata_only() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["show", "ADR-0001", "--metadata-only"])
        .assert()
        .success()
        .stdout(predicate::str::contains("ID:"))
        .stdout(predicate::str::contains("Title:"))
        .stdout(predicate::str::contains("Status:"));
}

#[test]
fn test_show_not_found() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["show", "ADR-9999"])
        .assert()
        .failure()
        .stderr(predicate::str::contains("ADR not found"));
}

#[test]
fn test_show_json_metadata_only() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["show", "ADR-0001", "--format", "json", "--metadata-only"])
        .assert()
        .success()
        .stdout(predicate::str::contains(r#""id": "ADR-0001""#))
        .stdout(predicate::str::contains(r#""title": "Use PostgreSQL""#))
        .stdout(predicate::str::contains(r#""status": "accepted""#))
        // metadata_only should NOT include body
        .stdout(predicate::str::contains("body").not());
}

#[test]
fn test_show_yaml_metadata_only() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["show", "ADR-0001", "--format", "yaml", "--metadata-only"])
        .assert()
        .success()
        .stdout(predicate::str::contains("title: Use PostgreSQL"))
        .stdout(predicate::str::contains("status: accepted"));
}
