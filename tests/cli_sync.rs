//! Integration tests for the `git-adr sync` command.

#![allow(deprecated)]

use assert_cmd::Command;
use predicates::prelude::*;
use std::process::Command as StdCommand;
use tempfile::TempDir;

/// Create a temporary git repository with an ADR and a remote.
fn setup_test_repo_with_remote() -> (TempDir, TempDir) {
    // Create the "remote" bare repository
    let remote_dir = TempDir::new().expect("Failed to create remote directory");
    StdCommand::new("git")
        .args(["init", "--bare"])
        .current_dir(remote_dir.path())
        .output()
        .expect("Failed to init bare repo");

    // Create the local repository
    let local_dir = TempDir::new().expect("Failed to create local directory");
    let path = local_dir.path();

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

    // Add the remote
    StdCommand::new("git")
        .args(["remote", "add", "origin", remote_dir.path().to_str().unwrap()])
        .current_dir(path)
        .output()
        .expect("Failed to add remote");

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

    // Push to remote
    StdCommand::new("git")
        .args(["push", "-u", "origin", "HEAD:main"])
        .current_dir(path)
        .output()
        .expect("Failed to push to remote");

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

    (local_dir, remote_dir)
}

#[test]
fn test_sync_push() {
    let (local_dir, _remote_dir) = setup_test_repo_with_remote();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(local_dir.path())
        .args(["sync", "--push"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Syncing with remote"))
        .stderr(predicate::str::contains("Pushed ADR notes"));
}

#[test]
fn test_sync_pull() {
    let (local_dir, _remote_dir) = setup_test_repo_with_remote();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(local_dir.path())
        .args(["sync", "--pull"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Fetching notes"));
}

#[test]
fn test_sync_both() {
    let (local_dir, _remote_dir) = setup_test_repo_with_remote();

    // Default behavior is both fetch and push
    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(local_dir.path())
        .arg("sync")
        .assert()
        .success()
        .stderr(predicate::str::contains("Syncing with remote"))
        .stderr(predicate::str::contains("Sync complete"));
}

#[test]
fn test_sync_custom_remote() {
    let (local_dir, remote_dir) = setup_test_repo_with_remote();

    // Add another remote
    StdCommand::new("git")
        .args(["remote", "add", "upstream", remote_dir.path().to_str().unwrap()])
        .current_dir(local_dir.path())
        .output()
        .expect("Failed to add upstream remote");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(local_dir.path())
        .args(["sync", "upstream", "--push"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Syncing with remote: upstream"));
}
