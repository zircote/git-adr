//! Integration tests for the `git-adr supersede` command.

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
        .args([
            "new",
            "Original Decision",
            "--status",
            "accepted",
            "--tag",
            "api",
        ])
        .assert()
        .success();

    // Create a new commit so supersede has a fresh commit to attach the new ADR to
    // (git notes can only have one note per commit)
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
fn test_supersede_creates_new_adr() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["supersede", "ADR-0001", "Improved Decision"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Superseding ADR"))
        .stderr(predicate::str::contains("Created new ADR: ADR-0002"))
        .stderr(predicate::str::contains(
            "Updated ADR-0001 status to superseded",
        ));

    // Verify old ADR is superseded
    let mut show_cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    show_cmd
        .current_dir(temp_dir.path())
        .args(["show", "ADR-0001", "--format", "json"])
        .assert()
        .success()
        .stdout(predicate::str::contains(r#""status": "superseded""#));

    // Verify new ADR exists and references old one
    let mut show_new_cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    show_new_cmd
        .current_dir(temp_dir.path())
        .args(["show", "ADR-0002", "--format", "json"])
        .assert()
        .success()
        .stdout(predicate::str::contains(r#""title": "Improved Decision""#));
}

#[test]
fn test_supersede_inherits_tags() {
    let temp_dir = setup_test_repo_with_adr();

    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(temp_dir.path())
        .args(["supersede", "ADR-0001", "Improved Decision"])
        .assert()
        .success();

    // Verify new ADR has inherited tags
    let mut show_cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    show_cmd
        .current_dir(temp_dir.path())
        .args(["show", "ADR-0002", "--format", "json"])
        .assert()
        .success()
        .stdout(predicate::str::contains("api"));
}

#[test]
fn test_supersede_not_found() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["supersede", "ADR-9999", "New Decision"])
        .assert()
        .failure()
        .stderr(predicate::str::contains("ADR not found"));
}
