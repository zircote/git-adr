//! Integration tests for the `git-adr stats` command.

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

    // Create several ADRs (each on a separate commit)
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(path)
        .args(["new", "First Decision", "--status", "accepted", "--tag", "api"])
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
        .args(["new", "Second Decision", "--status", "proposed", "--tag", "database"])
        .assert()
        .success();

    // Create new commit for third ADR
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
        .args(["new", "Third Decision", "--status", "rejected", "--tag", "api"])
        .assert()
        .success();

    temp_dir
}

#[test]
fn test_stats_text_output() {
    let temp_dir = setup_test_repo_with_adrs();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .arg("stats")
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR Statistics"))
        .stdout(predicate::str::contains("Total ADRs:"))
        .stdout(predicate::str::contains("3"))
        .stdout(predicate::str::contains("By Status:"));
}

#[test]
fn test_stats_json_output() {
    let temp_dir = setup_test_repo_with_adrs();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["stats", "--format", "json"])
        .assert()
        .success()
        .stdout(predicate::str::contains(r#""total": 3"#))
        .stdout(predicate::str::contains(r#""by_status""#))
        .stdout(predicate::str::contains(r#""by_tag""#));
}

#[test]
fn test_stats_shows_tags() {
    let temp_dir = setup_test_repo_with_adrs();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .arg("stats")
        .assert()
        .success()
        .stdout(predicate::str::contains("Top Tags:"))
        .stdout(predicate::str::contains("api"));
}

#[test]
fn test_stats_empty_repo() {
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
        .arg("stats")
        .assert()
        .success()
        .stdout(predicate::str::contains("Total ADRs:"))
        .stdout(predicate::str::contains("0"));
}
