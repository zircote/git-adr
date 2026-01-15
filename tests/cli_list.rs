//! Integration tests for the `git-adr list` command.

#![allow(deprecated)]

use assert_cmd::Command;
use predicates::prelude::*;
use std::process::Command as StdCommand;
use tempfile::TempDir;

/// Create a temporary git repository with ADR notes initialized.
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

    // Initialize ADR config
    StdCommand::new("git")
        .args(["config", "adr.initialized", "true"])
        .current_dir(path)
        .output()
        .expect("Failed to set adr.initialized");

    temp_dir
}

/// Add an ADR note to the test repository.
fn add_adr_note(path: &std::path::Path, id: &str, title: &str, status: &str) {
    let content = format!(
        r#"---
id: {id}
title: {title}
status: {status}
date: '2025-01-15'
tags:
  - test
---

# {title}

## Context

Test ADR content.
"#
    );

    // Get HEAD commit
    let output = StdCommand::new("git")
        .args(["rev-parse", "HEAD"])
        .current_dir(path)
        .output()
        .expect("Failed to get HEAD");
    let commit = String::from_utf8_lossy(&output.stdout).trim().to_string();

    // Add note
    StdCommand::new("git")
        .args(["notes", "--ref", "adr", "add", "-f", "-m", &content, &commit])
        .current_dir(path)
        .output()
        .expect("Failed to add ADR note");
}

#[test]
fn test_list_empty_repo() {
    let temp_dir = setup_test_repo();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .arg("list")
        .assert()
        .success()
        .stderr(predicate::str::contains("No ADRs found"));
}

#[test]
fn test_list_with_adrs() {
    let temp_dir = setup_test_repo();
    let path = temp_dir.path();

    // Add some ADR notes
    add_adr_note(path, "ADR-0001", "First Decision", "proposed");

    // Create another commit for a second ADR
    std::fs::write(path.join("file1.txt"), "content").expect("Failed to write file");
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

    add_adr_note(path, "ADR-0002", "Second Decision", "accepted");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .arg("list")
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR-0001"))
        .stdout(predicate::str::contains("ADR-0002"))
        .stdout(predicate::str::contains("2 ADR(s) found"));
}

#[test]
fn test_list_filter_by_status() {
    let temp_dir = setup_test_repo();
    let path = temp_dir.path();

    add_adr_note(path, "ADR-0001", "Proposed Decision", "proposed");

    std::fs::write(path.join("file1.txt"), "content").expect("Failed to write file");
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

    add_adr_note(path, "ADR-0002", "Accepted Decision", "accepted");

    // Filter by proposed
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["list", "--status", "proposed"])
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR-0001"))
        .stdout(predicate::str::contains("1 ADR(s) found"));

    // Filter by accepted
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["list", "--status", "accepted"])
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR-0002"))
        .stdout(predicate::str::contains("1 ADR(s) found"));
}

#[test]
fn test_list_json_format() {
    let temp_dir = setup_test_repo();
    let path = temp_dir.path();

    add_adr_note(path, "ADR-0001", "Test Decision", "proposed");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["list", "--format", "json"])
        .assert()
        .success()
        .stdout(predicate::str::contains(r#""id": "ADR-0001""#))
        .stdout(predicate::str::contains(r#""status": "proposed""#));
}

#[test]
fn test_list_csv_format() {
    let temp_dir = setup_test_repo();
    let path = temp_dir.path();

    add_adr_note(path, "ADR-0001", "Test Decision", "proposed");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["list", "--format", "csv"])
        .assert()
        .success()
        .stdout(predicate::str::contains("id,status,title,date,tags,commit"))
        .stdout(predicate::str::contains("ADR-0001"));
}

#[test]
fn test_list_oneline_format() {
    let temp_dir = setup_test_repo();
    let path = temp_dir.path();

    add_adr_note(path, "ADR-0001", "Test Decision", "proposed");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["list", "--format", "oneline"])
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR-0001"))
        .stdout(predicate::str::contains("Test Decision"));
}

#[test]
fn test_list_not_a_repo() {
    let temp_dir = TempDir::new().expect("Failed to create temp directory");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .arg("list")
        .assert()
        .failure()
        .stderr(predicate::str::contains("not a git repository"));
}

/// Add an ADR note with a specific tag.
fn add_adr_note_with_tag(path: &std::path::Path, id: &str, title: &str, status: &str, tag: &str) {
    let content = format!(
        r#"---
id: {id}
title: {title}
status: {status}
date: '2025-01-15'
tags:
  - {tag}
---

# {title}

## Context

Test ADR content.
"#
    );

    let output = StdCommand::new("git")
        .args(["rev-parse", "HEAD"])
        .current_dir(path)
        .output()
        .expect("Failed to get HEAD");
    let commit = String::from_utf8_lossy(&output.stdout).trim().to_string();

    StdCommand::new("git")
        .args(["notes", "--ref", "adr", "add", "-f", "-m", &content, &commit])
        .current_dir(path)
        .output()
        .expect("Failed to add ADR note");
}

#[test]
fn test_list_filter_by_tag() {
    let temp_dir = setup_test_repo();
    let path = temp_dir.path();

    add_adr_note_with_tag(path, "ADR-0001", "API Decision", "proposed", "api");

    std::fs::write(path.join("file1.txt"), "content").expect("Failed to write file");
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

    add_adr_note_with_tag(path, "ADR-0002", "Database Decision", "accepted", "database");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["list", "--tag", "api"])
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR-0001"))
        .stdout(predicate::str::contains("1 ADR(s) found"));
}

#[test]
fn test_list_reverse() {
    let temp_dir = setup_test_repo();
    let path = temp_dir.path();

    add_adr_note(path, "ADR-0001", "First Decision", "proposed");

    std::fs::write(path.join("file1.txt"), "content").expect("Failed to write file");
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

    add_adr_note(path, "ADR-0002", "Second Decision", "accepted");

    // Test with reverse flag
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["list", "--reverse"])
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR-0002"));
}

#[test]
fn test_list_oneline_all_statuses() {
    let temp_dir = setup_test_repo();
    let path = temp_dir.path();

    // Create ADRs with different statuses
    add_adr_note(path, "ADR-0001", "Deprecated Decision", "deprecated");

    std::fs::write(path.join("file1.txt"), "content").expect("Failed to write file");
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

    add_adr_note(path, "ADR-0002", "Superseded Decision", "superseded");

    std::fs::write(path.join("file2.txt"), "content").expect("Failed to write file");
    StdCommand::new("git")
        .args(["add", "."])
        .current_dir(path)
        .output()
        .expect("Failed to stage");
    StdCommand::new("git")
        .args(["commit", "-m", "Third commit"])
        .current_dir(path)
        .output()
        .expect("Failed to commit");

    add_adr_note(path, "ADR-0003", "Rejected Decision", "rejected");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["list", "--format", "oneline"])
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR-0001"))
        .stdout(predicate::str::contains("ADR-0002"))
        .stdout(predicate::str::contains("ADR-0003"));
}

/// Add an ADR note with a specific date.
fn add_adr_note_with_date(path: &std::path::Path, id: &str, title: &str, status: &str, date: &str) {
    let content = format!(
        r#"---
id: {id}
title: {title}
status: {status}
date: '{date}'
tags:
  - test
---

# {title}

## Context

Test ADR content.
"#
    );

    let output = StdCommand::new("git")
        .args(["rev-parse", "HEAD"])
        .current_dir(path)
        .output()
        .expect("Failed to get HEAD");
    let commit = String::from_utf8_lossy(&output.stdout).trim().to_string();

    StdCommand::new("git")
        .args(["notes", "--ref", "adr", "add", "-f", "-m", &content, &commit])
        .current_dir(path)
        .output()
        .expect("Failed to add ADR note");
}

#[test]
fn test_list_filter_since() {
    let temp_dir = setup_test_repo();
    let path = temp_dir.path();

    // Create an ADR with an old date
    add_adr_note_with_date(path, "ADR-0001", "Old Decision", "accepted", "2020-01-01");

    std::fs::write(path.join("file1.txt"), "content").expect("Failed to write file");
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

    // Create an ADR with a recent date
    add_adr_note_with_date(path, "ADR-0002", "Recent Decision", "proposed", "2025-01-01");

    // Filter to only show ADRs since 2024
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["list", "--since", "2024-01-01"])
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR-0002"))
        .stdout(predicate::str::contains("1 ADR(s) found"));
}

#[test]
fn test_list_filter_until() {
    let temp_dir = setup_test_repo();
    let path = temp_dir.path();

    // Create an ADR with an old date
    add_adr_note_with_date(path, "ADR-0001", "Old Decision", "accepted", "2020-01-01");

    std::fs::write(path.join("file1.txt"), "content").expect("Failed to write file");
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

    // Create an ADR with a recent date
    add_adr_note_with_date(path, "ADR-0002", "Recent Decision", "proposed", "2025-01-01");

    // Filter to only show ADRs until 2022
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["list", "--until", "2022-01-01"])
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR-0001"))
        .stdout(predicate::str::contains("1 ADR(s) found"));
}

#[test]
fn test_list_invalid_date_format() {
    let temp_dir = setup_test_repo();
    let path = temp_dir.path();

    add_adr_note(path, "ADR-0001", "Test Decision", "proposed");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["list", "--since", "not-a-date"])
        .assert()
        .failure()
        .stderr(predicate::str::contains("Invalid date format"));
}

#[test]
fn test_list_invalid_status() {
    let temp_dir = setup_test_repo();
    let path = temp_dir.path();

    add_adr_note(path, "ADR-0001", "Test Decision", "proposed");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["list", "--status", "invalid_status"])
        .assert()
        .failure()
        .stderr(predicate::str::contains("invalid status"));
}

#[test]
fn test_list_long_title_truncation() {
    let temp_dir = setup_test_repo();
    let path = temp_dir.path();

    // Create an ADR with a very long title (more than 50 chars to trigger truncation)
    let long_title = "This is a very very very very long title that should be truncated in table view";
    add_adr_note(path, "ADR-0001", long_title, "proposed");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["list"])
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR-0001"))
        // Verify the title is truncated (contains ... at the end)
        .stdout(predicate::str::contains("..."));
}

#[test]
fn test_list_all_statuses_table_format() {
    let temp_dir = setup_test_repo();
    let path = temp_dir.path();

    // Create ADRs with all status types (for table format)
    add_adr_note(path, "ADR-0001", "Proposed Decision", "proposed");

    // Create new commits for each subsequent ADR
    for (i, (id, title, status)) in [
        ("ADR-0002", "Accepted Decision", "accepted"),
        ("ADR-0003", "Deprecated Decision", "deprecated"),
        ("ADR-0004", "Superseded Decision", "superseded"),
        ("ADR-0005", "Rejected Decision", "rejected"),
    ]
    .iter()
    .enumerate()
    {
        std::fs::write(path.join(format!("file{}.txt", i + 1)), "content")
            .expect("Failed to write file");
        StdCommand::new("git")
            .args(["add", "."])
            .current_dir(path)
            .output()
            .expect("Failed to stage");
        StdCommand::new("git")
            .args(["commit", "-m", &format!("Commit {}", i + 2)])
            .current_dir(path)
            .output()
            .expect("Failed to commit");
        add_adr_note(path, id, title, status);
    }

    // Test table format (default)
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .arg("list")
        .assert()
        .success()
        .stdout(predicate::str::contains("proposed"))
        .stdout(predicate::str::contains("accepted"))
        .stdout(predicate::str::contains("deprecated"))
        .stdout(predicate::str::contains("superseded"))
        .stdout(predicate::str::contains("rejected"))
        .stdout(predicate::str::contains("5 ADR(s) found"));

    // Test oneline format with all statuses
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["list", "--format", "oneline"])
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR-0001"))
        .stdout(predicate::str::contains("ADR-0002"))
        .stdout(predicate::str::contains("ADR-0003"))
        .stdout(predicate::str::contains("ADR-0004"))
        .stdout(predicate::str::contains("ADR-0005"));
}

#[test]
fn test_list_filter_since_rfc3339() {
    let temp_dir = setup_test_repo();
    let path = temp_dir.path();

    add_adr_note_with_date(path, "ADR-0001", "Recent Decision", "proposed", "2025-01-01");

    // Use RFC3339 format for --since
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["list", "--since", "2024-01-01T00:00:00Z"])
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR-0001"));
}
