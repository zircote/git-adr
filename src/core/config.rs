//! Configuration management for git-adr.
//!
//! This module handles loading and saving configuration from git config.

use crate::core::Git;
use crate::Error;

/// Configuration for git-adr.
#[derive(Debug, Clone)]
pub struct AdrConfig {
    /// Prefix for ADR IDs (default: "ADR-").
    pub prefix: String,
    /// Number of digits in ADR ID (default: 4).
    pub digits: u8,
    /// Default template name.
    pub template: String,
    /// Default format (nygard, madr, etc.).
    pub format: String,
    /// Whether the repository is initialized for ADRs.
    pub initialized: bool,
}

impl Default for AdrConfig {
    fn default() -> Self {
        Self {
            prefix: "ADR-".to_string(),
            digits: 4,
            template: "default".to_string(),
            format: "nygard".to_string(),
            initialized: false,
        }
    }
}

/// Manager for ADR configuration.
#[derive(Debug)]
pub struct ConfigManager {
    git: Git,
}

impl ConfigManager {
    /// Create a new `ConfigManager`.
    #[must_use]
    pub const fn new(git: Git) -> Self {
        Self { git }
    }

    /// Load configuration from git config.
    ///
    /// # Errors
    ///
    /// Returns an error if configuration cannot be loaded.
    pub fn load(&self) -> Result<AdrConfig, Error> {
        let mut config = AdrConfig::default();

        // Check if initialized
        if let Some(val) = self.git.config_get("adr.initialized")? {
            config.initialized = val == "true";
        }

        // Load prefix
        if let Some(val) = self.git.config_get("adr.prefix")? {
            config.prefix = val;
        }

        // Load digits
        if let Some(val) = self.git.config_get("adr.digits")? {
            if let Ok(digits) = val.parse::<u8>() {
                config.digits = digits;
            }
        }

        // Load template
        if let Some(val) = self.git.config_get("adr.template")? {
            config.template = val;
        }

        // Load format
        if let Some(val) = self.git.config_get("adr.format")? {
            config.format = val;
        }

        Ok(config)
    }

    /// Save configuration to git config.
    ///
    /// # Errors
    ///
    /// Returns an error if configuration cannot be saved.
    pub fn save(&self, config: &AdrConfig) -> Result<(), Error> {
        self.git
            .config_set("adr.initialized", &config.initialized.to_string())?;
        self.git.config_set("adr.prefix", &config.prefix)?;
        self.git
            .config_set("adr.digits", &config.digits.to_string())?;
        self.git.config_set("adr.template", &config.template)?;
        self.git.config_set("adr.format", &config.format)?;

        Ok(())
    }

    /// Initialize ADR in the repository.
    ///
    /// # Errors
    ///
    /// Returns an error if initialization fails.
    pub fn initialize(&self, config: &AdrConfig) -> Result<(), Error> {
        // Verify we're in a git repository
        self.git.check_repository()?;

        // Save configuration
        let mut init_config = config.clone();
        init_config.initialized = true;
        self.save(&init_config)?;

        Ok(())
    }

    /// Check if ADR is initialized in this repository.
    ///
    /// # Errors
    ///
    /// Returns an error if the check fails.
    pub fn is_initialized(&self) -> Result<bool, Error> {
        let config = self.load()?;
        Ok(config.initialized)
    }

    /// Get a specific config value.
    ///
    /// # Errors
    ///
    /// Returns an error if the value cannot be retrieved.
    pub fn get(&self, key: &str) -> Result<Option<String>, Error> {
        self.git.config_get(&format!("adr.{key}"))
    }

    /// Set a specific config value.
    ///
    /// # Errors
    ///
    /// Returns an error if the value cannot be set.
    pub fn set(&self, key: &str, value: &str) -> Result<(), Error> {
        self.git.config_set(&format!("adr.{key}"), value)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::process::Command as StdCommand;
    use tempfile::TempDir;

    fn setup_git_repo() -> TempDir {
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

    #[test]
    fn test_default_config() {
        let config = AdrConfig::default();
        assert_eq!(config.prefix, "ADR-");
        assert_eq!(config.digits, 4);
        assert_eq!(config.template, "default");
        assert_eq!(config.format, "nygard");
        assert!(!config.initialized);
    }

    #[test]
    fn test_custom_config() {
        let config = AdrConfig {
            prefix: "DECISION-".to_string(),
            digits: 3,
            template: "madr".to_string(),
            format: "madr".to_string(),
            initialized: true,
        };
        assert_eq!(config.prefix, "DECISION-");
        assert_eq!(config.digits, 3);
        assert_eq!(config.template, "madr");
        assert!(config.initialized);
    }

    #[test]
    fn test_config_clone() {
        let config = AdrConfig::default();
        let cloned = config.clone();
        assert_eq!(config.prefix, cloned.prefix);
        assert_eq!(config.digits, cloned.digits);
    }

    #[test]
    fn test_config_manager_new() {
        let git = Git::new();
        let _manager = ConfigManager::new(git);
        // Just verify it creates without panic
    }

    #[test]
    fn test_config_initialize() {
        let temp_dir = setup_git_repo();
        let git = Git::with_work_dir(temp_dir.path());
        let manager = ConfigManager::new(git);

        let config = AdrConfig {
            prefix: "TEST-".to_string(),
            digits: 5,
            template: "madr".to_string(),
            format: "madr".to_string(),
            initialized: false,
        };

        let result = manager.initialize(&config);
        assert!(result.is_ok());

        // Verify the config was saved with initialized=true
        let loaded = manager.load().expect("Should load config");
        assert!(loaded.initialized);
        assert_eq!(loaded.prefix, "TEST-");
        assert_eq!(loaded.digits, 5);
    }

    #[test]
    fn test_config_load_save() {
        let temp_dir = setup_git_repo();
        let git = Git::with_work_dir(temp_dir.path());
        let manager = ConfigManager::new(git);

        let config = AdrConfig {
            prefix: "CUSTOM-".to_string(),
            digits: 6,
            template: "nygard".to_string(),
            format: "nygard".to_string(),
            initialized: true,
        };

        manager.save(&config).expect("Should save config");
        let loaded = manager.load().expect("Should load config");

        assert_eq!(loaded.prefix, "CUSTOM-");
        assert_eq!(loaded.digits, 6);
        assert!(loaded.initialized);
    }

    #[test]
    fn test_config_is_initialized() {
        let temp_dir = setup_git_repo();
        let git = Git::with_work_dir(temp_dir.path());
        let manager = ConfigManager::new(git);

        // Not initialized initially
        assert!(!manager.is_initialized().expect("Should check"));

        // Initialize
        let config = AdrConfig::default();
        manager.initialize(&config).expect("Should initialize");

        // Now it should be initialized
        assert!(manager.is_initialized().expect("Should check"));
    }

    #[test]
    fn test_config_get_set() {
        let temp_dir = setup_git_repo();
        let git = Git::with_work_dir(temp_dir.path());
        let manager = ConfigManager::new(git);

        // Set a custom value
        manager.set("custom", "value").expect("Should set");

        // Get the value
        let result = manager.get("custom").expect("Should get");
        assert_eq!(result, Some("value".to_string()));

        // Get non-existent value
        let result = manager.get("nonexistent").expect("Should get");
        assert_eq!(result, None);
    }
}
