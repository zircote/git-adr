//! Integration tests for the `git-adr config` command.

#![allow(deprecated)]

use assert_cmd::Command;
use predicates::prelude::*;
use std::process::Command as StdCommand;
use tempfile::TempDir;

/// Create a temporary git repository with ADR initialized.
fn setup_test_repo() -> TempDir {
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

    temp_dir
}

#[test]
fn test_config_list() {
    let temp_dir = setup_test_repo();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["config", "list"])
        .assert()
        .success()
        .stderr(predicate::str::contains("ADR Configuration"))
        .stdout(predicate::str::contains("adr.initialized"))
        .stdout(predicate::str::contains("adr.prefix"));
}

#[test]
fn test_config_get() {
    let temp_dir = setup_test_repo();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["config", "get", "prefix"])
        .assert()
        .success()
        .stdout(predicate::str::contains("ADR-"));
}

#[test]
fn test_config_get_not_set() {
    let temp_dir = setup_test_repo();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["config", "get", "nonexistent"])
        .assert()
        .failure()
        .stderr(predicate::str::contains("not set"));
}

#[test]
fn test_config_set() {
    let temp_dir = setup_test_repo();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["config", "set", "prefix", "ARCH-"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Set adr.prefix = ARCH-"));

    // Verify the change
    let mut get_cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    get_cmd
        .current_dir(temp_dir.path())
        .args(["config", "get", "prefix"])
        .assert()
        .success()
        .stdout(predicate::str::contains("ARCH-"));
}

#[test]
fn test_config_set_unknown_key() {
    let temp_dir = setup_test_repo();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["config", "set", "unknownkey", "value"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Unknown config key"))
        .stderr(predicate::str::contains("Setting anyway"));
}

#[test]
fn test_config_unset() {
    let temp_dir = setup_test_repo();

    // First set a value
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(temp_dir.path())
        .args(["config", "set", "template", "nygard"])
        .assert()
        .success();

    // Then unset it
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["config", "unset", "template"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Unset adr.template"));
}
