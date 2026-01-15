//! Integration tests for the `git-adr search` command.

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

    // Create several ADRs with different content (each on a separate commit)
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["new", "Use PostgreSQL for database"])
        .assert()
        .success();

    // Create a new commit for second ADR
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
        .args(["new", "Use Redis for caching"])
        .assert()
        .success();

    // Create a new commit for third ADR
    std::fs::write(path.join("file2.txt"), "content2").expect("Failed to write file");
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

    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["new", "Use Kafka for messaging"])
        .assert()
        .success();

    temp_dir
}

#[test]
fn test_search_finds_match() {
    let temp_dir = setup_test_repo_with_adrs();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["search", "PostgreSQL"])
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR-0001"))
        .stdout(predicate::str::contains("PostgreSQL"));
}

#[test]
fn test_search_default_case_insensitive() {
    let temp_dir = setup_test_repo_with_adrs();

    // Default search should be case insensitive
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["search", "postgresql"])
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR-0001"));
}

#[test]
fn test_search_no_match() {
    let temp_dir = setup_test_repo_with_adrs();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["search", "nonexistent"])
        .assert()
        .success()
        .stderr(predicate::str::contains("No matches found"));
}

#[test]
fn test_search_regex() {
    let temp_dir = setup_test_repo_with_adrs();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["search", "Use.*for", "--regex"])
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR-0001"))
        .stdout(predicate::str::contains("ADR-0002"))
        .stdout(predicate::str::contains("ADR-0003"));
}

#[test]
fn test_search_with_context() {
    let temp_dir = setup_test_repo_with_adrs();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["search", "PostgreSQL", "--context", "2"])
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR-0001"));
}

#[test]
fn test_search_case_sensitive() {
    let temp_dir = setup_test_repo_with_adrs();

    // With case-sensitive flag, should not match lowercase
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["search", "postgresql", "--case-sensitive"])
        .assert()
        .success()
        .stderr(predicate::str::contains("No matches found"));
}

#[test]
fn test_search_with_limit() {
    let temp_dir = setup_test_repo_with_adrs();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["search", "Use", "--limit", "1"])
        .assert()
        .success()
        // Should only return 1 result even though there are 3 matching ADRs
        .stdout(predicate::str::contains("ADR-0001"));
}

#[test]
fn test_search_filter_by_status() {
    let temp_dir = setup_test_repo_with_adrs();
    let path = temp_dir.path();

    // First, change one ADR's status to accepted
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["edit", "ADR-0001", "--status", "accepted"])
        .assert()
        .success();

    // Search with status filter - should only find the accepted ADR
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["search", "database", "--status", "accepted"])
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR-0001"))
        .stderr(predicate::str::contains("in 1 ADR(s)"));
}

#[test]
fn test_search_filter_by_tag() {
    let temp_dir = setup_test_repo_with_adrs();
    let path = temp_dir.path();

    // Add a tag to one ADR
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["edit", "ADR-0001", "--add-tag", "database"])
        .assert()
        .success();

    // Search with tag filter
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["search", "PostgreSQL", "--tag", "database"])
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR-0001"));
}

#[test]
fn test_search_case_sensitive_regex() {
    let temp_dir = setup_test_repo_with_adrs();

    // Case-sensitive regex search
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["search", "PostgreSQL", "--regex", "--case-sensitive"])
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR-0001"));
}
