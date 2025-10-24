"""Custom exceptions for pydantic-claude-cli."""

from __future__ import annotations


class PydanticClaudeCLIError(Exception):
    """Base exception for all pydantic-claude-cli errors."""

    pass


class ClaudeCLINotFoundError(PydanticClaudeCLIError):
    """Raised when Claude Code CLI is not found on the system."""

    def __init__(self, message: str | None = None):
        if message is None:
            message = (
                "Claude Code CLI not found. Please install it:\n"
                "\n"
                "1. Install Node.js from: https://nodejs.org/\n"
                "2. Install Claude Code CLI:\n"
                "   npm install -g @anthropic-ai/claude-code\n"
                "\n"
                "For more information, see: https://docs.anthropic.com/en/docs/claude-code"
            )
        super().__init__(message)


class MessageConversionError(PydanticClaudeCLIError):
    """Raised when message format conversion fails."""

    pass


class ToolIntegrationError(PydanticClaudeCLIError):
    """Raised when tool integration encounters an error."""

    pass


class ClaudeCLIProcessError(PydanticClaudeCLIError):
    """Raised when Claude CLI subprocess fails."""

    def __init__(self, message: str, exit_code: int | None = None):
        self.exit_code = exit_code
        if exit_code is not None:
            message = f"{message} (exit code: {exit_code})"
        super().__init__(message)
