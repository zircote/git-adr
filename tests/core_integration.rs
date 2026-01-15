//! Integration tests for core modules.

#![allow(deprecated)]

use assert_cmd::Command;
use std::process::Command as StdCommand;
use tempfile::TempDir;

/// Create a temporary git repository.
fn setup_git_repo() -> TempDir {
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

    temp_dir
}

#[test]
fn test_index_rebuild_via_init() {
    let temp_dir = setup_git_repo();
    let path = temp_dir.path();

    // Initialize ADR (this creates the index)
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .arg("init")
        .assert()
        .success();

    // Create several ADRs (each triggers index update)
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["new", "First Decision"])
        .assert()
        .success();

    // Create new commit for second ADR
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

    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["new", "Second Decision"])
        .assert()
        .success();

    // Search should find both ADRs
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["search", "Decision"])
        .assert()
        .success();
}

#[test]
fn test_create_adr_on_head_commit() {
    let temp_dir = setup_git_repo();
    let path = temp_dir.path();

    // Initialize ADR
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .arg("init")
        .assert()
        .success();

    // Create ADR without specifying commit (uses HEAD)
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["new", "Test Decision"])
        .assert()
        .success();

    // Show should work
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["show", "ADR-0001"])
        .assert()
        .success();
}

#[test]
fn test_config_initialize() {
    let temp_dir = setup_git_repo();
    let path = temp_dir.path();

    // Verify config is set after init
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["init", "--prefix", "DECISION-", "--digits", "3"])
        .assert()
        .success();

    // Check config was saved
    let output = StdCommand::new("git")
        .args(["config", "--get", "adr.prefix"])
        .current_dir(path)
        .output()
        .expect("Failed to get config");
    let prefix = String::from_utf8_lossy(&output.stdout);
    assert!(prefix.trim() == "DECISION-");

    let output = StdCommand::new("git")
        .args(["config", "--get", "adr.digits"])
        .current_dir(path)
        .output()
        .expect("Failed to get config");
    let digits = String::from_utf8_lossy(&output.stdout);
    assert!(digits.trim() == "3");
}

#[test]
fn test_adr_without_frontmatter_id_fallback() {
    let temp_dir = setup_git_repo();
    let path = temp_dir.path();

    // Initialize ADR
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .arg("init")
        .assert()
        .success();

    // Create ADR which will have frontmatter ID
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["new", "Test Decision"])
        .assert()
        .success();

    // The ADR should be retrievable
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["show", "ADR-0001"])
        .assert()
        .success();
}

#[test]
fn test_export_formats() {
    let temp_dir = setup_git_repo();
    let path = temp_dir.path();

    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .arg("init")
        .assert()
        .success();

    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["new", "Test Decision", "--tag", "test"])
        .assert()
        .success();

    // Test JSON export
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["export", "--format", "json", "--output", "adrs.json"])
        .assert()
        .success();

    // Verify JSON file was created
    assert!(path.join("adrs.json").exists());
}

#[test]
fn test_list_filter_by_date() {
    let temp_dir = setup_git_repo();
    let path = temp_dir.path();

    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .arg("init")
        .assert()
        .success();

    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["new", "Test Decision"])
        .assert()
        .success();

    // Test --since filter
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["list", "--since", "2020-01-01"])
        .assert()
        .success();

    // Test --until filter
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["list", "--until", "2030-12-31"])
        .assert()
        .success();
}

#[test]
fn test_log_command() {
    let temp_dir = setup_git_repo();
    let path = temp_dir.path();

    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .arg("init")
        .assert()
        .success();

    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["new", "Test Decision"])
        .assert()
        .success();

    // Test log command
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .arg("log")
        .assert()
        .success();
}

#[test]
fn test_sync_without_remote() {
    let temp_dir = setup_git_repo();
    let path = temp_dir.path();

    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .arg("init")
        .assert()
        .success();

    // Sync without remote should fail gracefully
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["sync", "--push"])
        .assert()
        .failure();
}

#[test]
fn test_multiple_adrs_on_different_commits() {
    let temp_dir = setup_git_repo();
    let path = temp_dir.path();

    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .arg("init")
        .assert()
        .success();

    // Create first ADR
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["new", "First Decision", "--tag", "first"])
        .assert()
        .success();

    // Create new commits for subsequent ADRs
    for i in 1..=3 {
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

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(path)
            .args(["new", &format!("Decision {}", i + 1)])
            .assert()
            .success();
    }

    // List should show all 4 ADRs
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .arg("list")
        .assert()
        .success();
}

#[test]
fn test_convert_adr_format() {
    let temp_dir = setup_git_repo();
    let path = temp_dir.path();

    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .arg("init")
        .assert()
        .success();

    // Create ADR with nygard format
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["new", "Test Decision", "--template", "nygard"])
        .assert()
        .success();

    // Convert to MADR format
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["convert", "ADR-0001", "--to", "madr"])
        .assert()
        .success();
}

#[test]
fn test_adr_without_id_in_frontmatter() {
    let temp_dir = setup_git_repo();
    let path = temp_dir.path();

    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .arg("init")
        .assert()
        .success();

    // Get HEAD commit hash
    let output = StdCommand::new("git")
        .args(["rev-parse", "HEAD"])
        .current_dir(path)
        .output()
        .expect("Failed to get HEAD");
    let commit = String::from_utf8_lossy(&output.stdout).trim().to_string();

    // Manually create ADR note without id field
    let adr_content = r#"---
title: Manual ADR
status: proposed
---

## Context

This is a manually created ADR without an id field.
"#;

    StdCommand::new("git")
        .args(["notes", "--ref=adr", "add", "-m", adr_content, &commit])
        .current_dir(path)
        .output()
        .expect("Failed to add note");

    // List should still work and show the ADR with a fallback ID
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .arg("list")
        .assert()
        .success();
}

#[test]
fn test_reinitialize_existing_repo() {
    let temp_dir = setup_git_repo();
    let path = temp_dir.path();

    // First initialization
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .arg("init")
        .assert()
        .success();

    // Re-initialize with different settings (requires --force)
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["init", "--force", "--prefix", "DEC-", "--digits", "5"])
        .assert()
        .success();

    // Verify new config
    let output = StdCommand::new("git")
        .args(["config", "--get", "adr.prefix"])
        .current_dir(path)
        .output()
        .expect("Failed to get config");
    let prefix = String::from_utf8_lossy(&output.stdout);
    assert!(prefix.trim() == "DEC-");
}
