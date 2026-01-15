//! AI provider abstraction.

use crate::Error;

/// Supported AI providers.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AiProvider {
    /// Anthropic Claude.
    Anthropic,
    /// OpenAI GPT.
    OpenAi,
    /// Google Gemini.
    Google,
    /// Local Ollama.
    Ollama,
}

impl std::fmt::Display for AiProvider {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Anthropic => write!(f, "anthropic"),
            Self::OpenAi => write!(f, "openai"),
            Self::Google => write!(f, "google"),
            Self::Ollama => write!(f, "ollama"),
        }
    }
}

impl std::str::FromStr for AiProvider {
    type Err = Error;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "anthropic" | "claude" => Ok(Self::Anthropic),
            "openai" | "gpt" => Ok(Self::OpenAi),
            "google" | "gemini" => Ok(Self::Google),
            "ollama" | "local" => Ok(Self::Ollama),
            _ => Err(Error::InvalidProvider {
                provider: s.to_string(),
            }),
        }
    }
}

/// Configuration for an AI provider.
#[derive(Debug, Clone)]
pub struct ProviderConfig {
    /// The provider to use.
    pub provider: AiProvider,
    /// Model name (provider-specific).
    pub model: String,
    /// API key or endpoint.
    pub api_key: Option<String>,
    /// Base URL for the API.
    pub base_url: Option<String>,
    /// Temperature for generation.
    pub temperature: f32,
    /// Maximum tokens to generate.
    pub max_tokens: u32,
}

impl Default for ProviderConfig {
    fn default() -> Self {
        Self {
            provider: AiProvider::Anthropic,
            model: "claude-3-haiku-20240307".to_string(),
            api_key: None,
            base_url: None,
            temperature: 0.7,
            max_tokens: 2048,
        }
    }
}

impl ProviderConfig {
    /// Create a new config for the given provider.
    #[must_use]
    pub fn new(provider: AiProvider) -> Self {
        let model = match provider {
            AiProvider::Anthropic => "claude-3-haiku-20240307".to_string(),
            AiProvider::OpenAi => "gpt-4o-mini".to_string(),
            AiProvider::Google => "gemini-1.5-flash".to_string(),
            AiProvider::Ollama => "llama3.2".to_string(),
        };

        Self {
            provider,
            model,
            ..Default::default()
        }
    }

    /// Set the model.
    #[must_use]
    pub fn with_model(mut self, model: impl Into<String>) -> Self {
        self.model = model.into();
        self
    }

    /// Set the API key.
    #[must_use]
    pub fn with_api_key(mut self, key: impl Into<String>) -> Self {
        self.api_key = Some(key.into());
        self
    }

    /// Set the base URL.
    #[must_use]
    pub fn with_base_url(mut self, url: impl Into<String>) -> Self {
        self.base_url = Some(url.into());
        self
    }

    /// Set the temperature.
    #[must_use]
    pub fn with_temperature(mut self, temp: f32) -> Self {
        self.temperature = temp;
        self
    }

    /// Get the API key from config or environment.
    ///
    /// # Errors
    ///
    /// Returns an error if no API key is available.
    pub fn get_api_key(&self) -> Result<String, Error> {
        if let Some(key) = &self.api_key {
            return Ok(key.clone());
        }

        let env_var = match self.provider {
            AiProvider::Anthropic => "ANTHROPIC_API_KEY",
            AiProvider::OpenAi => "OPENAI_API_KEY",
            AiProvider::Google => "GOOGLE_API_KEY",
            AiProvider::Ollama => return Ok(String::new()), // Ollama doesn't need a key
        };

        std::env::var(env_var).map_err(|_| Error::AiNotConfigured {
            message: format!("{env_var} not set"),
        })
    }

    /// Get the base URL from config or environment.
    #[must_use]
    pub fn get_base_url(&self) -> Option<String> {
        if let Some(url) = &self.base_url {
            return Some(url.clone());
        }

        match self.provider {
            AiProvider::Ollama => Some(
                std::env::var("OLLAMA_HOST")
                    .unwrap_or_else(|_| "http://localhost:11434".to_string()),
            ),
            _ => None,
        }
    }
}
