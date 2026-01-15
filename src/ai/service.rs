//! AI service for ADR operations.

use crate::ai::ProviderConfig;
use crate::core::Adr;
use crate::Error;

/// AI service for ADR generation and enhancement.
#[derive(Debug)]
pub struct AiService {
    config: ProviderConfig,
}

impl AiService {
    /// Create a new AI service with the given configuration.
    #[must_use]
    pub fn new(config: ProviderConfig) -> Self {
        Self { config }
    }

    /// Generate an ADR from a title and context.
    ///
    /// # Errors
    ///
    /// Returns an error if generation fails.
    pub async fn generate_adr(&self, title: &str, context: &str) -> Result<Adr, Error> {
        let _api_key = self.config.get_api_key()?;

        // TODO: Implement using langchain-rust
        // For now, create a stub ADR
        let mut adr = Adr::new("DRAFT".to_string(), title.to_string());
        adr.body = format!(
            "## Context\n\n{context}\n\n## Decision\n\nTo be determined.\n\n## Consequences\n\nTo be determined."
        );

        Ok(adr)
    }

    /// Suggest improvements for an ADR.
    ///
    /// # Errors
    ///
    /// Returns an error if suggestion fails.
    pub async fn suggest_improvements(&self, adr: &Adr) -> Result<Vec<String>, Error> {
        let _api_key = self.config.get_api_key()?;

        // TODO: Implement using langchain-rust
        let _ = adr;
        Ok(vec![
            "Consider adding more context about the decision drivers.".to_string(),
            "The consequences section could be more detailed.".to_string(),
        ])
    }

    /// Generate a summary of an ADR.
    ///
    /// # Errors
    ///
    /// Returns an error if summarization fails.
    pub async fn summarize(&self, adr: &Adr) -> Result<String, Error> {
        let _api_key = self.config.get_api_key()?;

        // TODO: Implement using langchain-rust
        Ok(format!(
            "ADR {} proposes: {}",
            adr.id, adr.frontmatter.title
        ))
    }

    /// Suggest a status for an ADR based on its content.
    ///
    /// # Errors
    ///
    /// Returns an error if analysis fails.
    pub async fn suggest_status(&self, adr: &Adr) -> Result<String, Error> {
        let _api_key = self.config.get_api_key()?;

        // TODO: Implement using langchain-rust
        let _ = adr;
        Ok("proposed".to_string())
    }

    /// Generate tags for an ADR.
    ///
    /// # Errors
    ///
    /// Returns an error if tag generation fails.
    pub async fn generate_tags(&self, adr: &Adr) -> Result<Vec<String>, Error> {
        let _api_key = self.config.get_api_key()?;

        // TODO: Implement using langchain-rust
        let _ = adr;
        Ok(vec!["architecture".to_string(), "decision".to_string()])
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ai::AiProvider;

    #[tokio::test]
    #[ignore = "requires API key"]
    async fn test_generate_adr() {
        let config = ProviderConfig::new(AiProvider::Anthropic);
        let service = AiService::new(config);

        let adr = service
            .generate_adr("Test ADR", "Testing the AI service")
            .await
            .expect("ADR generation should succeed with valid API key");

        assert_eq!(adr.title(), "Test ADR");
    }
}
