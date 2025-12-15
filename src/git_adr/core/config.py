"""Configuration management for git-adr.

Configuration is stored in git config, supporting both local (repository)
and global (user) levels. This follows git's native configuration model.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from git_adr.core.git import Git


# Configuration key prefix
CONFIG_PREFIX = "adr"

# Default values
DEFAULTS: dict[str, Any] = {
    "namespace": "adr",
    "artifacts_namespace": "adr-artifacts",
    "template": "madr",
    "editor": None,  # Use $EDITOR, $VISUAL, or fallback chain
    "artifact_warn_size": 1048576,  # 1MB
    "artifact_max_size": 10485760,  # 10MB
    "sync.auto_push": False,
    "sync.auto_pull": True,
    "sync.merge_strategy": "union",
    "ai.provider": None,
    "ai.model": None,
    "ai.temperature": 0.7,
    "wiki.platform": None,  # auto-detect
    "wiki.auto_sync": False,
}


# Valid template names
VALID_TEMPLATES = {
    "madr",
    "nygard",
    "y-statement",
    "alexandrian",
    "business",
    "planguage",
}

# Valid AI providers
VALID_PROVIDERS = {
    "openai",
    "anthropic",
    "google",
    "bedrock",
    "azure",
    "ollama",
    "openrouter",
}

# Valid merge strategies
VALID_MERGE_STRATEGIES = {
    "union",
    "ours",
    "theirs",
    "cat_sort_uniq",
}


@dataclass
class Config:
    """git-adr configuration.

    Configuration is loaded from git config and provides access to
    all git-adr settings.
    """

    # Notes namespaces
    namespace: str = "adr"
    artifacts_namespace: str = "adr-artifacts"

    # Template settings
    template: str = "madr"

    # Editor settings
    editor: str | None = None

    # Artifact settings
    artifact_warn_size: int = 1048576  # 1MB
    artifact_max_size: int = 10485760  # 10MB

    # Sync settings
    sync_auto_push: bool = False
    sync_auto_pull: bool = True
    sync_merge_strategy: str = "union"

    # AI settings
    ai_provider: str | None = None
    ai_model: str | None = None
    ai_temperature: float = 0.7

    # Wiki settings
    wiki_platform: str | None = None
    wiki_auto_sync: bool = False

    # Custom templates (path to directory)
    custom_templates_dir: Path | None = None

    @property
    def notes_ref(self) -> str:
        """Get the full notes reference for ADRs."""
        return f"refs/notes/{self.namespace}"

    @property
    def artifacts_ref(self) -> str:
        """Get the full notes reference for artifacts."""
        return f"refs/notes/{self.artifacts_namespace}"


class ConfigManager:
    """Manages git-adr configuration.

    Provides methods to read, write, and validate configuration
    stored in git config.
    """

    def __init__(self, git: Git) -> None:
        """Initialize the config manager.

        Args:
            git: Git executor instance.
        """
        self._git = git
        self._cache: dict[str, str] = {}
        self._cache_valid = False

    def _full_key(self, key: str) -> str:
        """Get the full git config key.

        Args:
            key: Short key (e.g., "namespace").

        Returns:
            Full key (e.g., "adr.namespace").
        """
        if key.startswith(f"{CONFIG_PREFIX}."):
            return key
        return f"{CONFIG_PREFIX}.{key}"

    def _invalidate_cache(self) -> None:
        """Invalidate the configuration cache."""
        self._cache_valid = False
        self._cache.clear()

    def _ensure_cache(self, global_: bool = False) -> None:
        """Ensure the cache is populated.

        Args:
            global_: If True, load global config only.
        """
        if self._cache_valid:
            return

        all_config = self._git.config_list(global_=global_)

        # Filter to adr.* keys
        self._cache = {
            k: v for k, v in all_config.items() if k.startswith(f"{CONFIG_PREFIX}.")
        }
        self._cache_valid = True

    def get(
        self,
        key: str,
        *,
        global_: bool = False,
        default: str | None = None,
    ) -> str | None:
        """Get a configuration value.

        Args:
            key: Configuration key (without prefix).
            global_: If True, read from global config.
            default: Default value if not found.

        Returns:
            Configuration value, or default.
        """
        full_key = self._full_key(key)

        # Try git config directly (most accurate)
        value = self._git.config_get(full_key, global_=global_)
        if value is not None:
            return value

        # Check defaults
        short_key = key.replace(f"{CONFIG_PREFIX}.", "")
        if short_key in DEFAULTS and default is None:
            default_value = DEFAULTS[short_key]
            return str(default_value) if default_value is not None else None

        return default

    def get_int(
        self,
        key: str,
        *,
        global_: bool = False,
        default: int = 0,
    ) -> int:
        """Get an integer configuration value.

        Args:
            key: Configuration key.
            global_: If True, read from global config.
            default: Default value if not found.

        Returns:
            Integer configuration value.
        """
        value = self.get(key, global_=global_)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def get_float(
        self,
        key: str,
        *,
        global_: bool = False,
        default: float = 0.0,
    ) -> float:
        """Get a float configuration value.

        Args:
            key: Configuration key.
            global_: If True, read from global config.
            default: Default value if not found.

        Returns:
            Float configuration value.
        """
        value = self.get(key, global_=global_)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            return default

    def get_bool(
        self,
        key: str,
        *,
        global_: bool = False,
        default: bool = False,
    ) -> bool:
        """Get a boolean configuration value.

        Args:
            key: Configuration key.
            global_: If True, read from global config.
            default: Default value if not found.

        Returns:
            Boolean configuration value.
        """
        value = self.get(key, global_=global_)
        if value is None:
            return default

        return value.lower() in ("true", "yes", "1", "on")

    def set(
        self,
        key: str,
        value: str,
        *,
        global_: bool = False,
    ) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key.
            value: Value to set.
            global_: If True, set in global config.

        Raises:
            ValueError: If the value is invalid.
        """
        full_key = self._full_key(key)

        # Validate known keys
        self._validate_value(key, value)

        self._git.config_set(full_key, value, global_=global_)
        self._invalidate_cache()

    def unset(
        self,
        key: str,
        *,
        global_: bool = False,
    ) -> bool:
        """Unset a configuration value.

        Args:
            key: Configuration key.
            global_: If True, unset from global config.

        Returns:
            True if the key was removed, False if it didn't exist.
        """
        full_key = self._full_key(key)
        result = self._git.config_unset(full_key, global_=global_)
        self._invalidate_cache()
        return result

    def list_all(self, *, global_: bool = False) -> dict[str, str]:
        """List all git-adr configuration.

        Args:
            global_: If True, list only global config.

        Returns:
            Dictionary of configuration key-value pairs.
        """
        self._ensure_cache(global_=global_)
        return dict(self._cache)

    def _validate_value(self, key: str, value: str) -> None:
        """Validate a configuration value.

        Args:
            key: Configuration key.
            value: Value to validate.

        Raises:
            ValueError: If the value is invalid.
        """
        short_key = key.replace(f"{CONFIG_PREFIX}.", "")

        if short_key == "template" and value not in VALID_TEMPLATES:
            valid = ", ".join(sorted(VALID_TEMPLATES))
            raise ValueError(f"Invalid template: {value}. Valid templates: {valid}")

        if short_key == "ai.provider" and value and value not in VALID_PROVIDERS:
            valid = ", ".join(sorted(VALID_PROVIDERS))
            raise ValueError(f"Invalid AI provider: {value}. Valid providers: {valid}")

        if short_key == "sync.merge_strategy" and value not in VALID_MERGE_STRATEGIES:
            valid = ", ".join(sorted(VALID_MERGE_STRATEGIES))
            raise ValueError(
                f"Invalid merge strategy: {value}. Valid strategies: {valid}"
            )

    def load(self) -> Config:
        """Load the full configuration.

        Returns:
            Config instance with all settings.
        """
        return Config(
            namespace=self.get("namespace") or "adr",
            artifacts_namespace=self.get("artifacts_namespace") or "adr-artifacts",
            template=self.get("template") or "madr",
            editor=self.get("editor"),
            artifact_warn_size=self.get_int("artifact_warn_size", default=1048576),
            artifact_max_size=self.get_int("artifact_max_size", default=10485760),
            sync_auto_push=self.get_bool("sync.auto_push"),
            sync_auto_pull=self.get_bool("sync.auto_pull", default=True),
            sync_merge_strategy=self.get("sync.merge_strategy") or "union",
            ai_provider=self.get("ai.provider"),
            ai_model=self.get("ai.model"),
            ai_temperature=self.get_float("ai.temperature", default=0.7),
            wiki_platform=self.get("wiki.platform"),
            wiki_auto_sync=self.get_bool("wiki.auto_sync"),
            custom_templates_dir=_parse_path(self.get("custom_templates_dir")),
        )


def _parse_path(value: str | None) -> Path | None:
    """Parse a path value.

    Args:
        value: Path string or None.

    Returns:
        Path instance or None.
    """
    if value is None:
        return None
    return Path(value).expanduser()


# Configuration documentation for help text
CONFIG_DOCS: dict[str, str] = {
    "namespace": "Notes namespace for ADRs (default: adr)",
    "artifacts_namespace": "Notes namespace for artifacts (default: adr-artifacts)",
    "template": "Default ADR template format (madr, nygard, y-statement, etc.)",
    "editor": "Editor command override (default: $EDITOR or vim)",
    "artifact_warn_size": "Warn when attaching files larger than this (bytes)",
    "artifact_max_size": "Refuse to attach files larger than this (bytes)",
    "sync.auto_push": "Automatically push notes after creating/editing",
    "sync.auto_pull": "Automatically pull notes before listing/showing",
    "sync.merge_strategy": "Merge strategy for notes (union, ours, theirs)",
    "ai.provider": "AI provider (openai, anthropic, google, ollama, etc.)",
    "ai.model": "AI model name (e.g., gpt-4, claude-3-opus)",
    "ai.temperature": "AI temperature for generation (0.0-1.0)",
    "wiki.platform": "Wiki platform (github, gitlab, auto-detect)",
    "wiki.auto_sync": "Automatically sync to wiki after creating/editing",
    "custom_templates_dir": "Directory containing custom ADR templates",
}
