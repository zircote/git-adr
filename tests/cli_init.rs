//! Integration tests for the `git-adr init` command.

#![allow(deprecated)]

use assert_cmd::Command;
use predicates::prelude::*;
use std::process::Command as StdCommand;
use tempfile::TempDir;

/// Create an empty git repository.
fn create_empty_repo() -> TempDir {
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

    temp_dir
}

#[test]
fn test_init_success() {
    let temp_dir = create_empty_repo();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .arg("init")
        .assert()
        .success()
        .stderr(predicate::str::contains("Initializing git-adr"))
        .stderr(predicate::str::contains("git-adr initialized successfully"));

    // Verify config is set
    let output = StdCommand::new("git")
        .args(["config", "--get", "adr.initialized"])
        .current_dir(temp_dir.path())
        .output()
        .expect("Failed to get config");
    assert_eq!(String::from_utf8_lossy(&output.stdout).trim(), "true");
}

#[test]
fn test_init_with_custom_prefix() {
    let temp_dir = create_empty_repo();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["init", "--prefix", "ARCH-"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Prefix: ARCH-"));

    // Verify config is set
    let output = StdCommand::new("git")
        .args(["config", "--get", "adr.prefix"])
        .current_dir(temp_dir.path())
        .output()
        .expect("Failed to get config");
    assert_eq!(String::from_utf8_lossy(&output.stdout).trim(), "ARCH-");
}

#[test]
fn test_init_with_custom_digits() {
    let temp_dir = create_empty_repo();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["init", "--digits", "6"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Digits: 6"));
}

#[test]
fn test_init_already_initialized() {
    let temp_dir = create_empty_repo();

    // First init
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(temp_dir.path())
        .arg("init")
        .assert()
        .success();

    // Second init without force
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .arg("init")
        .assert()
        .success()
        .stderr(predicate::str::contains("already initialized"));
}

#[test]
fn test_init_force_reinitialize() {
    let temp_dir = create_empty_repo();

    // First init
    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(temp_dir.path())
        .arg("init")
        .assert()
        .success();

    // Second init with force
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["init", "--force"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Initializing git-adr"));
}

#[test]
fn test_init_not_a_repo() {
    let temp_dir = TempDir::new().expect("Failed to create temp directory");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .arg("init")
        .assert()
        .failure()
        .stderr(predicate::str::contains("not a git repository"));
}
