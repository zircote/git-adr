//! Integration tests for the `git-adr new` command.

#![allow(deprecated)]

use assert_cmd::Command;
use predicates::prelude::*;
use std::process::Command as StdCommand;
use tempfile::TempDir;

/// Create a temporary git repository with ADR initialized.
fn setup_test_repo() -> TempDir {
    let temp_dir = TempDir::new().expect("Failed to create temp directory");
    let path = temp_dir.path();

    // Initialize git repo
    StdCommand::new("git")
        .args(["init"])
        .current_dir(path)
        .output()
        .expect("Failed to init git repo");

    // Configure git user for commits
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

    // Create initial commit
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

    // Initialize ADR using init command
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .arg("init")
        .assert()
        .success();

    temp_dir
}

#[test]
fn test_new_creates_adr() {
    let temp_dir = setup_test_repo();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["new", "Use PostgreSQL for data storage"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Creating new ADR"))
        .stderr(predicate::str::contains("Created ADR: ADR-0001"));

    // Verify ADR exists
    let mut list_cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    list_cmd
        .current_dir(temp_dir.path())
        .arg("list")
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR-0001"))
        .stdout(predicate::str::contains("Use PostgreSQL"));
}

#[test]
fn test_new_with_status() {
    let temp_dir = setup_test_repo();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["new", "Accepted Decision", "--status", "accepted"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Status: accepted"));

    // Verify status in list
    let mut list_cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    list_cmd
        .current_dir(temp_dir.path())
        .args(["list", "--format", "json"])
        .assert()
        .success()
        .stdout(predicate::str::contains("\"status\": \"accepted\""));
}

#[test]
fn test_new_with_tags() {
    let temp_dir = setup_test_repo();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["new", "Tagged Decision", "--tag", "database", "--tag", "infrastructure"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Tags: database, infrastructure"));
}

#[test]
fn test_new_increments_id() {
    let temp_dir = setup_test_repo();

    // Create first ADR
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(temp_dir.path())
        .args(["new", "First Decision"])
        .assert()
        .success()
        .stderr(predicate::str::contains("ADR-0001"));

    // Create second ADR
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(temp_dir.path())
        .args(["new", "Second Decision"])
        .assert()
        .success()
        .stderr(predicate::str::contains("ADR-0002"));
}

#[test]
fn test_new_preview_mode() {
    let temp_dir = setup_test_repo();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["new", "Preview Decision", "--preview"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Preview mode"))
        .stdout(predicate::str::contains("# Preview Decision"));

    // Verify ADR was NOT created
    let mut list_cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    list_cmd
        .current_dir(temp_dir.path())
        .arg("list")
        .assert()
        .success()
        .stderr(predicate::str::contains("No ADRs found"));
}

#[test]
fn test_new_without_init() {
    let temp_dir = TempDir::new().expect("Failed to create temp directory");
    let path = temp_dir.path();

    // Initialize git repo but NOT adr
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

    std::fs::write(path.join("README.md"), "# Test\n").expect("Failed to write README");
    StdCommand::new("git")
        .args(["add", "."])
        .current_dir(path)
        .output()
        .expect("Failed to stage");
    StdCommand::new("git")
        .args(["commit", "-m", "Initial commit"])
        .current_dir(path)
        .output()
        .expect("Failed to commit");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["new", "Some Decision"])
        .assert()
        .failure()
        .stderr(predicate::str::contains("not initialized"));
}

#[test]
fn test_new_with_deciders() {
    let temp_dir = setup_test_repo();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args([
            "new",
            "Decision with Deciders",
            "--deciders",
            "Alice",
            "--deciders",
            "Bob",
        ])
        .assert()
        .success()
        .stderr(predicate::str::contains("Created ADR"));

    // Verify deciders in show output
    let mut show_cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    show_cmd
        .current_dir(temp_dir.path())
        .args(["show", "ADR-0001", "--format", "json"])
        .assert()
        .success()
        .stdout(predicate::str::contains("Alice"))
        .stdout(predicate::str::contains("Bob"));
}

#[test]
fn test_new_with_link_to_commit() {
    let temp_dir = setup_test_repo();
    let path = temp_dir.path();

    // Get the HEAD commit
    let output = StdCommand::new("git")
        .args(["rev-parse", "HEAD"])
        .current_dir(path)
        .output()
        .expect("Failed to get HEAD");
    let head_commit = String::from_utf8_lossy(&output.stdout).trim().to_string();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["new", "Linked Decision", "--link", &head_commit])
        .assert()
        .success()
        .stderr(predicate::str::contains("Created ADR"));
}

#[test]
fn test_new_from_file_plain_body() {
    let temp_dir = setup_test_repo();
    let path = temp_dir.path();

    // Create a file with plain body content (no frontmatter)
    let body_content = "## Custom Context\n\nThis is custom content from a file.";
    std::fs::write(path.join("adr_body.md"), body_content).expect("Failed to write body file");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["new", "File Decision", "--file", "adr_body.md"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Created ADR"));

    // Verify the body was used
    let mut show_cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    show_cmd
        .current_dir(path)
        .args(["show", "ADR-0001"])
        .assert()
        .success()
        .stdout(predicate::str::contains("Custom Context"))
        .stdout(predicate::str::contains("custom content from a file"));
}

#[test]
fn test_new_from_file_with_frontmatter() {
    let temp_dir = setup_test_repo();
    let path = temp_dir.path();

    // Create a file with frontmatter (must include id to preserve it)
    let file_content = r#"---
id: ADR-0001
title: Custom Title from File
status: accepted
tags:
  - from-file
---

## Custom Body

Content from the file with frontmatter.
"#;
    std::fs::write(path.join("full_adr.md"), file_content).expect("Failed to write full ADR file");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["new", "Will Be Overwritten", "--file", "full_adr.md"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Created ADR"));

    // Verify the file content was used (including frontmatter overriding the title)
    let mut show_cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    show_cmd
        .current_dir(path)
        .args(["show", "ADR-0001", "--format", "json"])
        .assert()
        .success()
        .stdout(predicate::str::contains("Custom Title from File"))
        .stdout(predicate::str::contains("accepted"))
        .stdout(predicate::str::contains("from-file"));
}

#[test]
fn test_new_with_template() {
    let temp_dir = setup_test_repo();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["new", "MADR Decision", "--template", "madr"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Created ADR"));

    // Verify MADR template was used
    let mut show_cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    show_cmd
        .current_dir(temp_dir.path())
        .args(["show", "ADR-0001"])
        .assert()
        .success()
        .stdout(predicate::str::contains("Context and Problem Statement"));
}
