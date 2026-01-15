//! AI-powered features for git-adr.
//!
//! This module provides AI-assisted capabilities using langchain-rust:
//! - ADR generation from context
//! - Content suggestions
//! - Summary generation
//! - Status recommendations

use crate::Error;

mod provider;
mod service;

pub use provider::{AiProvider, ProviderConfig};
pub use service::AiService;

/// Check if AI features are available.
#[must_use]
pub fn is_available() -> bool {
    true
}

/// Get the default AI provider from environment.
///
/// # Errors
///
/// Returns an error if no provider is configured.
pub fn default_provider() -> Result<AiProvider, Error> {
    // Check for API keys in order of preference
    if std::env::var("ANTHROPIC_API_KEY").is_ok() {
        return Ok(AiProvider::Anthropic);
    }
    if std::env::var("OPENAI_API_KEY").is_ok() {
        return Ok(AiProvider::OpenAi);
    }
    if std::env::var("GOOGLE_API_KEY").is_ok() {
        return Ok(AiProvider::Google);
    }
    if std::env::var("OLLAMA_HOST").is_ok() {
        return Ok(AiProvider::Ollama);
    }

    Err(Error::AiNotConfigured {
        message: "No AI provider configured. Set ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY, or OLLAMA_HOST.".to_string(),
    })
}
