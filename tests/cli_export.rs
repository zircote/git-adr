//! Integration tests for the `git-adr export` command.

#![allow(deprecated)]

use assert_cmd::Command;
use predicates::prelude::*;
use std::process::Command as StdCommand;
use tempfile::TempDir;

/// Create a temporary git repository with ADRs.
fn setup_test_repo_with_adrs() -> TempDir {
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
        .args(["new", "First Decision", "--tag", "api"])
        .assert()
        .success();

    // Create a new commit for the second ADR
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

    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["new", "Second Decision", "--tag", "database"])
        .assert()
        .success();

    temp_dir
}

#[test]
fn test_export_markdown() {
    let temp_dir = setup_test_repo_with_adrs();
    let export_dir = temp_dir.path().join("export-md");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args([
            "export",
            "--output",
            export_dir.to_str().unwrap(),
            "--format",
            "markdown",
        ])
        .assert()
        .success()
        .stderr(predicate::str::contains("Exporting"))
        .stderr(predicate::str::contains("2 ADR(s)"))
        .stderr(predicate::str::contains("Exported"));

    // Verify files were created
    assert!(export_dir.join("ADR-0001.md").exists());
    assert!(export_dir.join("ADR-0002.md").exists());
    assert!(export_dir.join("index.md").exists());
}

#[test]
fn test_export_json() {
    let temp_dir = setup_test_repo_with_adrs();
    let export_dir = temp_dir.path().join("export-json");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args([
            "export",
            "--output",
            export_dir.to_str().unwrap(),
            "--format",
            "json",
        ])
        .assert()
        .success();

    // Verify files were created
    assert!(export_dir.join("ADR-0001.json").exists());
    assert!(export_dir.join("ADR-0002.json").exists());
    assert!(export_dir.join("index.json").exists());

    // Verify JSON content
    let content = std::fs::read_to_string(export_dir.join("ADR-0001.json")).unwrap();
    assert!(content.contains("\"id\": \"ADR-0001\""));
}

#[test]
fn test_export_html() {
    let temp_dir = setup_test_repo_with_adrs();
    let export_dir = temp_dir.path().join("export-html");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args([
            "export",
            "--output",
            export_dir.to_str().unwrap(),
            "--format",
            "html",
        ])
        .assert()
        .success();

    // Verify files were created
    assert!(export_dir.join("ADR-0001.html").exists());
    assert!(export_dir.join("index.html").exists());

    // Verify HTML content
    let content = std::fs::read_to_string(export_dir.join("index.html")).unwrap();
    assert!(content.contains("<!DOCTYPE html>"));
    assert!(content.contains("Architecture Decision Records"));
}

#[test]
fn test_export_filter_by_status() {
    let temp_dir = setup_test_repo_with_adrs();

    // Change one ADR to accepted
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(temp_dir.path())
        .args(["edit", "ADR-0001", "--status", "accepted"])
        .assert()
        .success();

    let export_dir = temp_dir.path().join("export-filtered");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args([
            "export",
            "--output",
            export_dir.to_str().unwrap(),
            "--status",
            "accepted",
        ])
        .assert()
        .success()
        .stderr(predicate::str::contains("1 ADR(s)"));

    // Only accepted ADR should be exported
    assert!(export_dir.join("ADR-0001.md").exists());
    assert!(!export_dir.join("ADR-0002.md").exists());
}

#[test]
fn test_export_empty() {
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

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["export", "--output", "export"])
        .assert()
        .success()
        .stderr(predicate::str::contains("No ADRs to export"));
}

#[test]
fn test_export_filter_by_tag() {
    let temp_dir = setup_test_repo_with_adrs();
    let export_dir = temp_dir.path().join("export-tag-filtered");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args([
            "export",
            "--output",
            export_dir.to_str().unwrap(),
            "--tag",
            "api",
        ])
        .assert()
        .success()
        .stderr(predicate::str::contains("1 ADR(s)"));

    // Only the ADR with 'api' tag should be exported
    assert!(export_dir.join("ADR-0001.md").exists());
    assert!(!export_dir.join("ADR-0002.md").exists());
}

#[test]
fn test_export_html_with_code_blocks() {
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

    // Create ADR
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["new", "Code Block Decision"])
        .assert()
        .success();

    // Get HEAD commit hash
    let output = StdCommand::new("git")
        .args(["rev-parse", "HEAD"])
        .current_dir(path)
        .output()
        .expect("Failed to get HEAD");
    let commit = String::from_utf8_lossy(&output.stdout).trim().to_string();

    // Directly modify the note to add code blocks
    let adr_content = r#"---
id: ADR-0001
title: Code Block Decision
status: proposed
date: 2025-01-15
tags: []
---

## Context

Here is some code:

```rust
fn main() {
    println!("Hello");
}
```

## Decision

We decided to use Rust."#;

    StdCommand::new("git")
        .args([
            "notes",
            "--ref=adr",
            "add",
            "-f",
            "-m",
            adr_content,
            &commit,
        ])
        .current_dir(path)
        .output()
        .expect("Failed to update note");

    let export_dir = path.join("export-code-html");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args([
            "export",
            "--output",
            export_dir.to_str().unwrap(),
            "--format",
            "html",
        ])
        .assert()
        .success();

    // Verify HTML contains code block conversion
    let content = std::fs::read_to_string(export_dir.join("ADR-0001.html")).unwrap();
    assert!(content.contains("<pre><code>"));
    assert!(content.contains("</code></pre>"));
}

#[test]
fn test_export_html_without_tags() {
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

    // Create ADR without any tags
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["new", "No Tags Decision"])
        .assert()
        .success();

    let export_dir = path.join("export-no-tags-html");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args([
            "export",
            "--output",
            export_dir.to_str().unwrap(),
            "--format",
            "html",
        ])
        .assert()
        .success();

    // Verify HTML was created without tag div
    let content = std::fs::read_to_string(export_dir.join("ADR-0001.html")).unwrap();
    assert!(content.contains("<!DOCTYPE html>"));
    // Should NOT have a tags div since there are no tags
    assert!(!content.contains("<div class=\"tags\">"));
}

#[test]
fn test_export_html_with_unclosed_code_block() {
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

    // Create ADR
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["new", "Unclosed Code Block"])
        .assert()
        .success();

    // Get HEAD commit hash
    let output = StdCommand::new("git")
        .args(["rev-parse", "HEAD"])
        .current_dir(path)
        .output()
        .expect("Failed to get HEAD");
    let commit = String::from_utf8_lossy(&output.stdout).trim().to_string();

    // Create ADR with unclosed code block
    let adr_content = r#"---
id: ADR-0001
title: Unclosed Code Block
status: proposed
date: 2025-01-15
tags: []
---

## Context

Here is an unclosed code block:

```rust
fn main() {
    println!("Never closed!");
}
"#;

    StdCommand::new("git")
        .args([
            "notes",
            "--ref=adr",
            "add",
            "-f",
            "-m",
            adr_content,
            &commit,
        ])
        .current_dir(path)
        .output()
        .expect("Failed to update note");

    let export_dir = path.join("export-unclosed-code");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args([
            "export",
            "--output",
            export_dir.to_str().unwrap(),
            "--format",
            "html",
        ])
        .assert()
        .success();

    // Verify HTML contains code block with auto-closed tags
    let content = std::fs::read_to_string(export_dir.join("ADR-0001.html")).unwrap();
    assert!(content.contains("<pre><code>"));
    // The unclosed code block should be auto-closed
    assert!(content.contains("</code></pre>"));
}
