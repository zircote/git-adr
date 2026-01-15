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

    #[test]
    fn test_default_config() {
        let config = AdrConfig::default();
        assert_eq!(config.prefix, "ADR-");
        assert_eq!(config.digits, 4);
        assert_eq!(config.template, "default");
        assert_eq!(config.format, "nygard");
        assert!(!config.initialized);
    }
}
