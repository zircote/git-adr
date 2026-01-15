//! Integration tests for the `git-adr edit` command.

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
        .args(["new", "Original Title", "--status", "proposed", "--tag", "original"])
        .assert()
        .success();

    temp_dir
}

#[test]
fn test_edit_change_status() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["edit", "ADR-0001", "--status", "accepted"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Editing ADR"))
        .stderr(predicate::str::contains("Status: proposed"))
        .stderr(predicate::str::contains("accepted"))
        .stderr(predicate::str::contains("ADR updated"));

    // Verify status changed
    let mut show_cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    show_cmd
        .current_dir(temp_dir.path())
        .args(["show", "ADR-0001", "--format", "json"])
        .assert()
        .success()
        .stdout(predicate::str::contains(r#""status": "accepted""#));
}

#[test]
fn test_edit_change_title() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["edit", "ADR-0001", "--title", "New Title"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Title: Original Title"))
        .stderr(predicate::str::contains("New Title"));

    // Verify title changed
    let mut show_cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    show_cmd
        .current_dir(temp_dir.path())
        .args(["show", "ADR-0001", "--format", "json"])
        .assert()
        .success()
        .stdout(predicate::str::contains(r#""title": "New Title""#));
}

#[test]
fn test_edit_add_tag() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["edit", "ADR-0001", "--add-tag", "newtag"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Added tag: newtag"));

    // Verify tag added
    let mut show_cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    show_cmd
        .current_dir(temp_dir.path())
        .args(["show", "ADR-0001", "--format", "json"])
        .assert()
        .success()
        .stdout(predicate::str::contains("newtag"));
}

#[test]
fn test_edit_remove_tag() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["edit", "ADR-0001", "--remove-tag", "original"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Removed tag: original"));
}

#[test]
fn test_edit_no_changes() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["edit", "ADR-0001"])
        .assert()
        .success()
        .stderr(predicate::str::contains("No changes specified"));
}

#[test]
fn test_edit_not_found() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["edit", "ADR-9999", "--status", "accepted"])
        .assert()
        .failure()
        .stderr(predicate::str::contains("ADR not found"));
}

#[test]
fn test_edit_add_tag_already_exists() {
    let temp_dir = setup_test_repo_with_adr();

    // Try to add the same tag that already exists
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["edit", "ADR-0001", "--add-tag", "original"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Tag already exists: original"));
}

#[test]
fn test_edit_remove_tag_not_found() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["edit", "ADR-0001", "--remove-tag", "nonexistent"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Tag not found: nonexistent"));
}

#[test]
fn test_edit_add_decider() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["edit", "ADR-0001", "--add-decider", "Alice"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Added decider: Alice"));

    // Verify decider added
    let mut show_cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    show_cmd
        .current_dir(temp_dir.path())
        .args(["show", "ADR-0001", "--format", "json"])
        .assert()
        .success()
        .stdout(predicate::str::contains("Alice"));
}

#[test]
fn test_edit_add_decider_already_exists() {
    let temp_dir = setup_test_repo_with_adr();

    // First add a decider
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(temp_dir.path())
        .args(["edit", "ADR-0001", "--add-decider", "Bob"])
        .assert()
        .success();

    // Try to add the same decider again
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["edit", "ADR-0001", "--add-decider", "Bob"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Decider already exists: Bob"));
}

#[test]
fn test_edit_remove_decider() {
    let temp_dir = setup_test_repo_with_adr();

    // First add a decider
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(temp_dir.path())
        .args(["edit", "ADR-0001", "--add-decider", "Charlie"])
        .assert()
        .success();

    // Now remove it
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["edit", "ADR-0001", "--remove-decider", "Charlie"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Removed decider: Charlie"));
}

#[test]
fn test_edit_remove_decider_not_found() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["edit", "ADR-0001", "--remove-decider", "Nobody"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Decider not found: Nobody"));
}

#[test]
fn test_edit_invalid_status() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["edit", "ADR-0001", "--status", "invalid_status"])
        .assert()
        .failure()
        .stderr(predicate::str::contains("invalid status"));
}
