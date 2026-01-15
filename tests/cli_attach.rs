//! Integration tests for the `git-adr attach` command.

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
fn test_attach_file() {
    let temp_dir = setup_test_repo_with_adr();
    let path = temp_dir.path();

    // Create a file to attach
    let attachment_content = "This is a test attachment";
    std::fs::write(path.join("attachment.txt"), attachment_content)
        .expect("Failed to write attachment");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["attach", "ADR-0001", "attachment.txt"])
        .assert()
        .success()
        .stderr(predicate::str::contains("Attaching"))
        .stderr(predicate::str::contains("attachment.txt"));
}

#[test]
fn test_attach_file_with_description() {
    let temp_dir = setup_test_repo_with_adr();
    let path = temp_dir.path();

    std::fs::write(path.join("diagram.png"), b"\x89PNG\r\n\x1a\n").expect("Failed to write file");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args([
            "attach",
            "ADR-0001",
            "diagram.png",
            "--description",
            "Architecture diagram",
        ])
        .assert()
        .success()
        .stderr(predicate::str::contains("Attached"));
}

#[test]
fn test_attach_file_not_found() {
    let temp_dir = setup_test_repo_with_adr();

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(temp_dir.path())
        .args(["attach", "ADR-0001", "nonexistent.txt"])
        .assert()
        .failure()
        .stderr(predicate::str::contains("File not found"));
}

#[test]
fn test_attach_adr_not_found() {
    let temp_dir = setup_test_repo_with_adr();
    let path = temp_dir.path();

    std::fs::write(path.join("file.txt"), "content").expect("Failed to write file");

    let mut cmd = Command::cargo_bin("git-adr").expect("Failed to find binary");
    cmd.current_dir(path)
        .args(["attach", "ADR-9999", "file.txt"])
        .assert()
        .failure()
        .stderr(predicate::str::contains("ADR not found"));
}
