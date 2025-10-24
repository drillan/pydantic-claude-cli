"""Provider implementation for Claude Code CLI."""

from __future__ import annotations

import shutil
from pathlib import Path

from pydantic_ai import ModelProfile
from pydantic_ai.providers import Provider

from .exceptions import ClaudeCLINotFoundError


class ClaudeCodeCLIProvider(Provider[None]):
    """Provider for Claude Code CLI.

    This provider uses the Claude Code CLI to interact with Claude models
    without requiring an API key. The CLI must be installed on the system.

    Example:
        ```python
        from pydantic_claude_cli import ClaudeCodeCLIProvider

        provider = ClaudeCodeCLIProvider()
        # or with custom CLI path
        provider = ClaudeCodeCLIProvider(cli_path="/custom/path/to/claude")
        ```
    """

    def __init__(self, cli_path: str | Path | None = None):
        """Initialize the Claude Code CLI provider.

        Args:
            cli_path: Optional custom path to the Claude CLI executable.
                     If not provided, will search in standard locations.

        Raises:
            ClaudeCLINotFoundError: If Claude CLI is not found on the system.
        """
        self._cli_path = self._find_cli(cli_path)

    def _find_cli(self, cli_path: str | Path | None) -> str:
        """Find Claude Code CLI binary.

        Args:
            cli_path: Optional custom path to the CLI executable.

        Returns:
            Path to the Claude CLI executable.

        Raises:
            ClaudeCLINotFoundError: If CLI is not found.
        """
        if cli_path:
            path = Path(cli_path)
            if path.exists() and path.is_file():
                return str(path)
            raise ClaudeCLINotFoundError(f"Claude CLI not found at specified path: {cli_path}")

        # Try to find in PATH
        if cli := shutil.which("claude"):
            return cli

        # Check common installation locations
        locations = [
            Path.home() / ".npm-global/bin/claude",
            Path("/usr/local/bin/claude"),
            Path.home() / ".local/bin/claude",
            Path.home() / "node_modules/.bin/claude",
            Path.home() / ".yarn/bin/claude",
        ]

        for path in locations:
            if path.exists() and path.is_file():
                return str(path)

        # CLI not found
        raise ClaudeCLINotFoundError()

    @property
    def name(self) -> str:
        """The provider name."""
        return "claude-code-cli"

    @property
    def base_url(self) -> str:
        """The base URL for the provider API.

        Since this uses the CLI, we return a local identifier.
        """
        return "local://claude-code-cli"

    @property
    def client(self) -> None:
        """The Claude SDK client.

        Note: We don't use a persistent client since we use the query() function
        for each request instead of ClaudeSDKClient.
        """
        return None

    def model_profile(self, model_name: str) -> ModelProfile | None:
        """Get the model profile for the named model.

        For Claude Code CLI, we delegate to Anthropic's model profiles
        since the underlying models are the same.

        Args:
            model_name: The name of the model.

        Returns:
            The model profile if available, None otherwise.
        """
        # Import here to avoid circular imports
        from pydantic_ai.profiles.anthropic import anthropic_model_profile

        return anthropic_model_profile(model_name)
