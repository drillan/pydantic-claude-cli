"""Claude Code CLI adapter for Pydantic AI.

This package enables using Claude models via Claude Code CLI without requiring
an API key. The Claude Code CLI must be installed on your system.

Example:
    ```python
    from pydantic_ai import Agent
    from pydantic_claude_cli import ClaudeCodeCLIModel

    # Create a model instance
    model = ClaudeCodeCLIModel('claude-3-5-sonnet-latest')

    # Use with Pydantic AI Agent
    agent = Agent(model, instructions='You are a helpful assistant')

    # Run a query
    result = await agent.run('Hello, Claude!')
    print(result.data)
    ```

Requirements:
    - Claude Code CLI must be installed: npm install -g @anthropic-ai/claude-code
    - You must be logged in to Claude Code
"""

from .exceptions import (
    ClaudeCLINotFoundError,
    ClaudeCLIProcessError,
    MessageConversionError,
    PydanticClaudeCLIError,
    ToolIntegrationError,
)
from .model import ClaudeCodeCLIModel
from .provider import ClaudeCodeCLIProvider

__version__ = "0.1.0"

__all__ = [
    # Main exports
    "ClaudeCodeCLIModel",
    "ClaudeCodeCLIProvider",
    # Exceptions
    "PydanticClaudeCLIError",
    "ClaudeCLINotFoundError",
    "ClaudeCLIProcessError",
    "MessageConversionError",
    "ToolIntegrationError",
]
