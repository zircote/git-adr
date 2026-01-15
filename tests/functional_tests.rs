//! Comprehensive functional tests for git-adr.
//!
//! These tests verify the tool works correctly in real-world scenarios,
//! including edge cases, error handling, and data integrity.

#![allow(deprecated)]

use assert_cmd::Command;
use predicates::prelude::*;
use std::process::Command as StdCommand;
use tempfile::TempDir;

// =============================================================================
// TEST UTILITIES
// =============================================================================

/// Create a basic git repository for testing.
fn create_git_repo() -> TempDir {
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

    temp_dir
}

/// Create a git repository with ADR initialized.
fn create_initialized_repo() -> TempDir {
    let temp_dir = create_git_repo();

    Command::cargo_bin("git-adr")
        .expect("Failed to find binary")
        .current_dir(temp_dir.path())
        .arg("init")
        .assert()
        .success();

    temp_dir
}

/// Create an additional commit in the repository.
fn create_commit(temp_dir: &TempDir, filename: &str, message: &str) {
    let path = temp_dir.path();
    std::fs::write(path.join(filename), format!("content for {filename}"))
        .expect("Failed to write file");
    StdCommand::new("git")
        .args(["add", "."])
        .current_dir(path)
        .output()
        .expect("Failed to stage");
    StdCommand::new("git")
        .args(["commit", "-m", message])
        .current_dir(path)
        .output()
        .expect("Failed to commit");
}

// =============================================================================
// EDGE CASES AND ERROR HANDLING TESTS
// =============================================================================

mod edge_cases {
    use super::*;

    #[test]
    fn test_init_not_in_git_repo() {
        let temp_dir = TempDir::new().expect("Failed to create temp directory");
        // Don't initialize git - just a plain directory

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .arg("init")
            .assert()
            .failure();
        // Error message may be in stdout or stderr depending on implementation
    }

    #[test]
    fn test_new_without_init() {
        let temp_dir = create_git_repo();
        // Don't initialize ADR

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "Test ADR"])
            .assert()
            .failure()
            .stderr(predicate::str::contains("not initialized"));
    }

    #[test]
    fn test_show_nonexistent_adr() {
        let temp_dir = create_initialized_repo();

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["show", "ADR-9999"])
            .assert()
            .failure()
            .stderr(predicate::str::contains("not found"));
    }

    #[test]
    fn test_edit_nonexistent_adr() {
        let temp_dir = create_initialized_repo();

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["edit", "ADR-9999", "--status", "accepted"])
            .assert()
            .failure()
            .stderr(predicate::str::contains("not found"));
    }

    #[test]
    fn test_rm_nonexistent_adr() {
        let temp_dir = create_initialized_repo();

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["rm", "ADR-9999", "--force"])
            .assert()
            .failure()
            .stderr(predicate::str::contains("not found"));
    }

    #[test]
    fn test_invalid_status() {
        let temp_dir = create_initialized_repo();

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "Test ADR"])
            .assert()
            .success();

        // Invalid status should fail
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["edit", "ADR-0001", "--status", "invalid_status"])
            .assert()
            .failure();
    }

    #[test]
    fn test_list_empty_repo() {
        let temp_dir = create_initialized_repo();

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .arg("list")
            .assert()
            .success()
            .stderr(predicate::str::contains("No ADRs found"));
    }

    #[test]
    fn test_search_empty_repo() {
        let temp_dir = create_initialized_repo();

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["search", "anything"])
            .assert()
            .success()
            .stderr(predicate::str::contains("No matches"));
    }

    #[test]
    fn test_stats_empty_repo() {
        let temp_dir = create_initialized_repo();

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .arg("stats")
            .assert()
            .success()
            .stdout(predicate::str::contains("Total ADRs: 0"));
    }

    #[test]
    fn test_export_empty_repo() {
        let temp_dir = create_initialized_repo();

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["export", "--output", "export"])
            .assert()
            .success()
            .stderr(predicate::str::contains("No ADRs to export"));
    }

    #[test]
    fn test_double_init_without_force() {
        let temp_dir = create_initialized_repo();

        // Try to init again without --force
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .arg("init")
            .assert()
            .success()
            .stderr(predicate::str::contains("already initialized"));
    }

    #[test]
    fn test_double_init_with_force() {
        let temp_dir = create_initialized_repo();

        // Init again with --force should succeed
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["init", "--force", "--prefix", "DEC-"])
            .assert()
            .success();

        // Verify new prefix is applied
        let output = StdCommand::new("git")
            .args(["config", "--get", "adr.prefix"])
            .current_dir(temp_dir.path())
            .output()
            .expect("Failed to get config");
        let prefix = String::from_utf8_lossy(&output.stdout);
        assert_eq!(prefix.trim(), "DEC-");
    }

    #[test]
    fn test_supersede_nonexistent_adr() {
        let temp_dir = create_initialized_repo();

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["supersede", "ADR-9999", "New Decision"])
            .assert()
            .failure()
            .stderr(predicate::str::contains("not found"));
    }

    #[test]
    fn test_link_nonexistent_adr() {
        let temp_dir = create_initialized_repo();

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["link", "ADR-9999", "ADR-0001", "--type", "relates"])
            .assert()
            .failure();
    }

    #[test]
    fn test_convert_nonexistent_adr() {
        let temp_dir = create_initialized_repo();

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["convert", "ADR-9999", "--to", "madr"])
            .assert()
            .failure()
            .stderr(predicate::str::contains("not found"));
    }

    #[test]
    fn test_partial_id_matching() {
        let temp_dir = create_initialized_repo();

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "Test ADR"])
            .assert()
            .success();

        // Should work with partial ID
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["show", "0001"])
            .assert()
            .success();

        // Should work with just number
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["show", "1"])
            .assert()
            .success();
    }
}

// =============================================================================
// DATA INTEGRITY TESTS
// =============================================================================

mod data_integrity {
    use super::*;

    #[test]
    fn test_adr_survives_new_commits() {
        let temp_dir = create_initialized_repo();

        // Create an ADR
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "Initial Decision"])
            .assert()
            .success();

        // Create several more commits
        for i in 1..5 {
            create_commit(&temp_dir, &format!("file{i}.txt"), &format!("Commit {i}"));
        }

        // ADR should still be accessible
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["show", "ADR-0001"])
            .assert()
            .success()
            .stdout(predicate::str::contains("Initial Decision"));
    }

    #[test]
    fn test_multiple_adrs_on_different_commits() {
        let temp_dir = create_initialized_repo();

        // Create ADR on initial commit
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "First Decision"])
            .assert()
            .success();

        // Create new commit and another ADR
        create_commit(&temp_dir, "file1.txt", "Second commit");
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "Second Decision"])
            .assert()
            .success();

        // Create another commit and ADR
        create_commit(&temp_dir, "file2.txt", "Third commit");
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "Third Decision"])
            .assert()
            .success();

        // All ADRs should be listed
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .arg("list")
            .assert()
            .success()
            .stdout(predicate::str::contains("ADR-0001"))
            .stdout(predicate::str::contains("ADR-0002"))
            .stdout(predicate::str::contains("ADR-0003"));
    }

    #[test]
    fn test_adr_survives_branch_and_merge() {
        let temp_dir = create_initialized_repo();

        // Create ADR on main branch
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "Main Branch Decision"])
            .assert()
            .success();

        // Create a feature branch
        StdCommand::new("git")
            .args(["checkout", "-b", "feature"])
            .current_dir(temp_dir.path())
            .output()
            .expect("Failed to create branch");

        create_commit(&temp_dir, "feature.txt", "Feature commit");

        // Go back to main
        StdCommand::new("git")
            .args(["checkout", "main"])
            .current_dir(temp_dir.path())
            .output()
            .expect("Failed to checkout main");

        // Create another commit on main
        create_commit(&temp_dir, "main.txt", "Main commit");

        // Merge feature branch
        StdCommand::new("git")
            .args(["merge", "feature", "-m", "Merge feature"])
            .current_dir(temp_dir.path())
            .output()
            .expect("Failed to merge");

        // ADR should still be accessible
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["show", "ADR-0001"])
            .assert()
            .success()
            .stdout(predicate::str::contains("Main Branch Decision"));
    }

    #[test]
    fn test_adr_content_preserved_after_edit() {
        let temp_dir = create_initialized_repo();

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "Original Title", "--tag", "original"])
            .assert()
            .success();

        // Edit to change status
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["edit", "ADR-0001", "--status", "accepted"])
            .assert()
            .success();

        // Add a tag
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["edit", "ADR-0001", "--add-tag", "new-tag"])
            .assert()
            .success();

        // Verify all content preserved
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["show", "ADR-0001"])
            .assert()
            .success()
            .stdout(predicate::str::contains("Original Title"))
            .stdout(predicate::str::contains("accepted"))
            .stdout(predicate::str::contains("original"))
            .stdout(predicate::str::contains("new-tag"));
    }

    #[test]
    fn test_search_index_consistency() {
        let temp_dir = create_initialized_repo();

        // Create ADRs
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "Database Decision", "--tag", "database"])
            .assert()
            .success();

        create_commit(&temp_dir, "file1.txt", "Commit 1");

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "API Decision", "--tag", "api"])
            .assert()
            .success();

        // Search should find correct ADRs
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["search", "database"])
            .assert()
            .success()
            .stdout(predicate::str::contains("ADR-0001"))
            .stdout(predicate::str::contains("Database Decision"));

        // Edit ADR title
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["edit", "ADR-0001", "--title", "PostgreSQL Decision"])
            .assert()
            .success();

        // Search should find updated content
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["search", "PostgreSQL"])
            .assert()
            .success()
            .stdout(predicate::str::contains("ADR-0001"));
    }

    #[test]
    fn test_rm_cleans_up_properly() {
        let temp_dir = create_initialized_repo();

        // Create ADR
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "To Be Deleted"])
            .assert()
            .success();

        // Verify it exists
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["show", "ADR-0001"])
            .assert()
            .success();

        // Delete it
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["rm", "ADR-0001", "--force"])
            .assert()
            .success();

        // Verify it's gone
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["show", "ADR-0001"])
            .assert()
            .failure();

        // List should show no ADRs
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .arg("list")
            .assert()
            .success()
            .stderr(predicate::str::contains("No ADRs found"));
    }
}

// =============================================================================
// END-TO-END COMMAND TESTS
// =============================================================================

mod end_to_end {
    use super::*;

    #[test]
    fn test_full_adr_lifecycle() {
        let temp_dir = create_initialized_repo();

        // 1. Create ADR
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "Use PostgreSQL", "--tag", "database"])
            .assert()
            .success();

        // 2. View it
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["show", "ADR-0001"])
            .assert()
            .success()
            .stdout(predicate::str::contains("Use PostgreSQL"))
            .stdout(predicate::str::contains("proposed"));

        // 3. Edit status to accepted
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["edit", "ADR-0001", "--status", "accepted"])
            .assert()
            .success();

        // 4. Add more tags
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["edit", "ADR-0001", "--add-tag", "infrastructure"])
            .assert()
            .success();

        // 5. Verify changes
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["show", "ADR-0001", "--metadata-only"])
            .assert()
            .success()
            .stdout(predicate::str::contains("accepted"))
            .stdout(predicate::str::contains("database"))
            .stdout(predicate::str::contains("infrastructure"));

        // 6. Create superseding ADR
        create_commit(&temp_dir, "file1.txt", "New commit");
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["supersede", "ADR-0001", "Use MySQL Instead"])
            .assert()
            .success();

        // 7. Verify original is superseded
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["show", "ADR-0001", "--metadata-only"])
            .assert()
            .success()
            .stdout(predicate::str::contains("superseded"));

        // 8. Check stats
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .arg("stats")
            .assert()
            .success()
            .stdout(predicate::str::contains("Total ADRs: 2"))
            .stdout(predicate::str::contains("superseded"));
    }

    #[test]
    fn test_all_export_formats() {
        let temp_dir = create_initialized_repo();

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "Test ADR", "--tag", "test"])
            .assert()
            .success();

        // Markdown export
        let md_dir = temp_dir.path().join("export-md");
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args([
                "export",
                "--format",
                "markdown",
                "--output",
                md_dir.to_str().unwrap(),
            ])
            .assert()
            .success();
        assert!(md_dir.join("ADR-0001.md").exists());
        assert!(md_dir.join("index.md").exists());

        // JSON export
        let json_dir = temp_dir.path().join("export-json");
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args([
                "export",
                "--format",
                "json",
                "--output",
                json_dir.to_str().unwrap(),
            ])
            .assert()
            .success();
        assert!(json_dir.join("ADR-0001.json").exists());
        let content = std::fs::read_to_string(json_dir.join("ADR-0001.json")).unwrap();
        assert!(content.contains("\"id\": \"ADR-0001\""));

        // HTML export
        let html_dir = temp_dir.path().join("export-html");
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args([
                "export",
                "--format",
                "html",
                "--output",
                html_dir.to_str().unwrap(),
            ])
            .assert()
            .success();
        assert!(html_dir.join("ADR-0001.html").exists());
        let content = std::fs::read_to_string(html_dir.join("ADR-0001.html")).unwrap();
        assert!(content.contains("<!DOCTYPE html>"));
    }

    #[test]
    fn test_all_template_formats() {
        let temp_dir = create_initialized_repo();

        let formats = [
            "nygard",
            "madr",
            "y-statement",
            "alexandrian",
            "business-case",
        ];

        for (i, format) in formats.iter().enumerate() {
            if i > 0 {
                create_commit(&temp_dir, &format!("file{i}.txt"), &format!("Commit {i}"));
            }

            Command::cargo_bin("git-adr")
                .expect("Failed to find binary")
                .current_dir(temp_dir.path())
                .args([
                    "new",
                    &format!("Decision using {}", format),
                    "--template",
                    format,
                ])
                .assert()
                .success();
        }

        // Verify all were created
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .arg("list")
            .assert()
            .success()
            .stdout(predicate::str::contains("5 ADR(s) found"));
    }

    #[test]
    fn test_convert_between_formats() {
        let temp_dir = create_initialized_repo();

        // Create with nygard format
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "Original ADR", "--template", "nygard"])
            .assert()
            .success();

        // Convert to MADR
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["convert", "ADR-0001", "--to", "madr"])
            .assert()
            .success();

        // Verify content is preserved
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["show", "ADR-0001"])
            .assert()
            .success()
            .stdout(predicate::str::contains("Original ADR"));
    }

    #[test]
    fn test_list_with_all_filters() {
        let temp_dir = create_initialized_repo();

        // Create ADRs with different statuses and tags
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "Proposed ADR", "--tag", "api"])
            .assert()
            .success();

        create_commit(&temp_dir, "file1.txt", "Commit 1");
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "Accepted ADR", "--tag", "database"])
            .assert()
            .success();
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["edit", "ADR-0002", "--status", "accepted"])
            .assert()
            .success();

        create_commit(&temp_dir, "file2.txt", "Commit 2");
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "Rejected ADR", "--tag", "frontend"])
            .assert()
            .success();
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["edit", "ADR-0003", "--status", "rejected"])
            .assert()
            .success();

        // Filter by status
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["list", "--status", "accepted"])
            .assert()
            .success()
            .stdout(predicate::str::contains("ADR-0002"))
            .stdout(predicate::str::contains("1 ADR(s) found"));

        // Filter by tag
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["list", "--tag", "api"])
            .assert()
            .success()
            .stdout(predicate::str::contains("ADR-0001"));
    }

    #[test]
    fn test_show_output_formats() {
        let temp_dir = create_initialized_repo();

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "Test ADR", "--tag", "test"])
            .assert()
            .success();

        // Markdown format (default)
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["show", "ADR-0001"])
            .assert()
            .success()
            .stdout(predicate::str::contains("---"))
            .stdout(predicate::str::contains("# Test ADR"));

        // YAML format
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["show", "ADR-0001", "--format", "yaml"])
            .assert()
            .success()
            .stdout(predicate::str::contains("id: ADR-0001"));

        // JSON format
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["show", "ADR-0001", "--format", "json"])
            .assert()
            .success()
            .stdout(predicate::str::contains("\"id\":"));

        // Metadata only
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["show", "ADR-0001", "--metadata-only"])
            .assert()
            .success()
            .stdout(predicate::str::contains("ID: ADR-0001"));
    }

    #[test]
    fn test_log_command() {
        let temp_dir = create_initialized_repo();

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "First ADR"])
            .assert()
            .success();

        create_commit(&temp_dir, "file1.txt", "Regular commit");
        create_commit(&temp_dir, "file2.txt", "Another commit");

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "Second ADR"])
            .assert()
            .success();

        // Log should show commits
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .arg("log")
            .assert()
            .success()
            .stderr(predicate::str::contains("commit(s) shown"));

        // Log with --linked-only
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["log", "--linked-only"])
            .assert()
            .success()
            .stdout(predicate::str::contains("ADR-"));
    }

    #[test]
    fn test_config_command() {
        let temp_dir = create_initialized_repo();

        // Get config
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["config", "list"])
            .assert()
            .success()
            .stdout(predicate::str::contains("prefix"))
            .stdout(predicate::str::contains("ADR-"));

        // Set config
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["config", "set", "prefix", "DEC-"])
            .assert()
            .success();

        // Verify change
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["config", "get", "prefix"])
            .assert()
            .success()
            .stdout(predicate::str::contains("DEC-"));
    }

    #[test]
    fn test_link_command() {
        let temp_dir = create_initialized_repo();

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "First ADR"])
            .assert()
            .success();

        create_commit(&temp_dir, "file1.txt", "Second commit");

        // Get HEAD commit for linking
        let output = StdCommand::new("git")
            .args(["rev-parse", "HEAD"])
            .current_dir(temp_dir.path())
            .output()
            .expect("Failed to get HEAD");
        let commit = String::from_utf8_lossy(&output.stdout).trim().to_string();

        // Link ADR to a different commit
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["link", "ADR-0001", &commit])
            .assert()
            .success();
    }

    #[test]
    fn test_stats_json_output() {
        let temp_dir = create_initialized_repo();

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "Test ADR", "--tag", "test"])
            .assert()
            .success();

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["stats", "--format", "json"])
            .assert()
            .success()
            .stdout(predicate::str::contains("\"total\":"))
            .stdout(predicate::str::contains("\"by_status\":"));
    }
}

// =============================================================================
// STRESS TESTS
// =============================================================================

mod stress {
    use super::*;

    #[test]
    fn test_many_adrs() {
        let temp_dir = create_initialized_repo();

        // Create 20 ADRs
        for i in 1..=20 {
            if i > 1 {
                create_commit(&temp_dir, &format!("file{i}.txt"), &format!("Commit {i}"));
            }
            Command::cargo_bin("git-adr")
                .expect("Failed to find binary")
                .current_dir(temp_dir.path())
                .args(["new", &format!("Decision {}", i)])
                .assert()
                .success();
        }

        // List should show all 20
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .arg("list")
            .assert()
            .success()
            .stdout(predicate::str::contains("20 ADR(s) found"));

        // Search should work
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["search", "Decision"])
            .assert()
            .success();

        // Stats should work
        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .arg("stats")
            .assert()
            .success()
            .stdout(predicate::str::contains("Total ADRs: 20"));
    }

    #[test]
    fn test_adr_with_many_tags() {
        let temp_dir = create_initialized_repo();

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args([
                "new",
                "Multi-tag ADR",
                "--tag",
                "tag1",
                "--tag",
                "tag2",
                "--tag",
                "tag3",
                "--tag",
                "tag4",
                "--tag",
                "tag5",
            ])
            .assert()
            .success();

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["show", "ADR-0001"])
            .assert()
            .success()
            .stdout(predicate::str::contains("tag1"))
            .stdout(predicate::str::contains("tag5"));
    }

    #[test]
    fn test_adr_with_special_characters_in_title() {
        let temp_dir = create_initialized_repo();

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["new", "Use API v2.0 (with OAuth 2.0)"])
            .assert()
            .success();

        Command::cargo_bin("git-adr")
            .expect("Failed to find binary")
            .current_dir(temp_dir.path())
            .args(["show", "ADR-0001"])
            .assert()
            .success()
            .stdout(predicate::str::contains("Use API v2.0 (with OAuth 2.0)"));
    }

    #[test]
    fn test_rapid_operations() {
        let temp_dir = create_initialized_repo();

        // Rapid create-edit-show cycles
        for i in 1..=5 {
            if i > 1 {
                create_commit(&temp_dir, &format!("file{i}.txt"), &format!("Commit {i}"));
            }

            let adr_id = format!("ADR-{:04}", i);

            // Create
            Command::cargo_bin("git-adr")
                .expect("Failed to find binary")
                .current_dir(temp_dir.path())
                .args(["new", &format!("Rapid ADR {}", i)])
                .assert()
                .success();

            // Immediately edit
            Command::cargo_bin("git-adr")
                .expect("Failed to find binary")
                .current_dir(temp_dir.path())
                .args(["edit", &adr_id, "--status", "accepted"])
                .assert()
                .success();

            // Immediately show
            Command::cargo_bin("git-adr")
                .expect("Failed to find binary")
                .current_dir(temp_dir.path())
                .args(["show", &adr_id])
                .assert()
                .success()
                .stdout(predicate::str::contains("accepted"));
        }
    }
}
