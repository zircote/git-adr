//! Integration tests for the `git-adr rm` command.

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
fn test_rm_with_force() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["rm", "ADR-0001", "--force"])
        .assert()
        .success()
        .stderr(predicate::str::contains("ADR: ADR-0001"))
        .stderr(predicate::str::contains("ADR removed"));

    // Verify ADR is deleted
    let mut list_cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    list_cmd
        .current_dir(temp_dir.path())
        .arg("list")
        .assert()
        .success()
        .stderr(predicate::str::contains("No ADRs found"));
}

#[test]
fn test_rm_not_found() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["rm", "ADR-9999", "--force"])
        .assert()
        .failure()
        .stderr(predicate::str::contains("ADR not found"));
}

#[test]
fn test_rm_partial_id() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["rm", "0001", "--force"])
        .assert()
        .success()
        .stderr(predicate::str::contains("ADR removed"));
}

#[test]
fn test_rm_interactive_confirm() {
    let temp_dir = setup_test_repo_with_adr();

    // Confirm deletion with 'y'
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["rm", "ADR-0001"])
        .write_stdin("y\n")
        .assert()
        .success()
        .stderr(predicate::str::contains("ADR removed"));
}

#[test]
fn test_rm_interactive_abort() {
    let temp_dir = setup_test_repo_with_adr();

    // Abort deletion with 'n'
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["rm", "ADR-0001"])
        .write_stdin("n\n")
        .assert()
        .success()
        .stderr(predicate::str::contains("Aborted"));

    // Verify ADR still exists
    let mut list_cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    list_cmd
        .current_dir(temp_dir.path())
        .arg("list")
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR-0001"));
}

#[test]
fn test_rm_interactive_default_abort() {
    let temp_dir = setup_test_repo_with_adr();

    // Empty input should abort (default is no)
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["rm", "ADR-0001"])
        .write_stdin("\n")
        .assert()
        .success()
        .stderr(predicate::str::contains("Aborted"));
}
