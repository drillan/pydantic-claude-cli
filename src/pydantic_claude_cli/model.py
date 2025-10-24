"""Model implementation for Claude Code CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from claude_code_sdk import query as claude_query
from claude_code_sdk.types import (
    AssistantMessage,
    ClaudeCodeOptions,
    Message,
    ResultMessage,
    SystemMessage,
)
from pydantic_ai import ModelProfile
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse
from pydantic_ai.models import Model, ModelRequestParameters, ModelSettings
from pydantic_ai.providers import Provider

from .exceptions import ClaudeCLIProcessError, MessageConversionError, ClaudeCLINotFoundError
from .message_converter import (
    convert_from_claude_message,
    convert_to_claude_prompt,
    extract_system_prompt,
    extract_usage_from_result,
)
from .provider import ClaudeCodeCLIProvider


@dataclass(init=False)
class ClaudeCodeCLIModel(Model):
    """A model that uses Claude Code CLI.

    This model enables using Claude models without an API key by leveraging
    the Claude Code CLI. The CLI must be installed on the system.

    Example:
        ```python
        from pydantic_ai import Agent
        from pydantic_claude_cli import ClaudeCodeCLIModel

        model = ClaudeCodeCLIModel('claude-3-5-sonnet-latest')
        agent = Agent(model, instructions='You are a helpful assistant')

        result = await agent.run('Hello, Claude!')
        print(result.data)
        ```

    Note:
        This initial implementation has the following limitations:
        - Only text-based messages are supported
        - Custom tools are not yet integrated
        - Multimodal content (images, files) is not yet supported
    """

    _model_name: str = field(repr=True)
    _provider: ClaudeCodeCLIProvider = field(repr=False)
    _cli_path: str | Path | None = field(default=None, repr=False)
    _max_turns: int | None = field(default=None, repr=False)
    _permission_mode: Literal["default", "acceptEdits", "plan", "bypassPermissions"] | None = field(
        default=None, repr=False
    )

    def __init__(
        self,
        model_name: str,
        *,
        provider: Literal["claude-code-cli"] | ClaudeCodeCLIProvider = "claude-code-cli",
        profile: ModelProfile | None = None,
        settings: ModelSettings | None = None,
        cli_path: str | Path | None = None,
        max_turns: int | None = None,
        permission_mode: Literal["default", "acceptEdits", "plan", "bypassPermissions"] | None = None,
    ):
        """Initialize Claude Code CLI model.

        Args:
            model_name: Name of the Claude model to use (e.g., 'claude-3-5-sonnet-latest').
            provider: Provider instance or 'claude-code-cli' string.
            profile: Model profile to use.
            settings: Default model settings.
            cli_path: Optional custom path to Claude CLI executable.
            max_turns: Maximum number of conversation turns (passed to CLI).
            permission_mode: Permission mode for the CLI.
        """
        self._model_name = model_name
        self._cli_path = cli_path
        self._max_turns = max_turns
        self._permission_mode = permission_mode

        if isinstance(provider, str):
            if provider == "claude-code-cli":
                provider = ClaudeCodeCLIProvider(cli_path=cli_path)
            else:
                raise ValueError(f"Unknown provider string: {provider}")

        self._provider = provider

        # Get profile from provider if not specified
        if profile is None and hasattr(self._provider, "model_profile"):
            profile = self._provider.model_profile(model_name)

        super().__init__(settings=settings, profile=profile)

    @property
    def model_name(self) -> str:
        """The model name."""
        return self._model_name

    @property
    def system(self) -> str:
        """The model system/provider name."""
        return self._provider.name

    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        """Make a non-streaming request to the model.

        Args:
            messages: List of messages in the conversation.
            model_settings: Optional model-specific settings.
            model_request_parameters: Request parameters including tools and output settings.

        Returns:
            Model response with generated content.

        Raises:
            MessageConversionError: If message conversion fails.
            ClaudeCLIProcessError: If the CLI process fails.
        """
        # Prepare settings
        model_settings, model_request_parameters = self.prepare_request(
            model_settings, model_request_parameters
        )

        # Check for unsupported features
        if model_request_parameters.function_tools or model_request_parameters.output_tools:
            raise MessageConversionError(
                "Custom tools are not yet supported by ClaudeCodeCLIModel. "
                "Only Claude Code CLI's built-in tools are available."
            )

        # Convert messages
        try:
            prompt = convert_to_claude_prompt(messages)
            system_prompt = extract_system_prompt(messages)
        except Exception as e:
            raise MessageConversionError(f"Failed to convert messages: {e}") from e

        # Prepare Claude Code options
        options = ClaudeCodeOptions(
            model=self._model_name,
            system_prompt=system_prompt,
            max_turns=self._max_turns,
            permission_mode=self._permission_mode,
            # Disable tools for now
            allowed_tools=[],
        )

        # Use the query() function for one-shot requests
        try:
            # Collect all messages
            response_messages: list[Message] = []
            async for message in claude_query(prompt=prompt, options=options):
                response_messages.append(message)

                # ResultMessage is the last message, but continue to consume
                # the generator to avoid cleanup errors
                if isinstance(message, ResultMessage):
                    # Don't break, let the generator finish naturally
                    pass

            # Find the assistant message(s) in the response
            assistant_messages: list[AssistantMessage] = []
            result_message: ResultMessage | None = None

            for msg in response_messages:
                if isinstance(msg, AssistantMessage):
                    assistant_messages.append(msg)
                elif isinstance(msg, ResultMessage):
                    result_message = msg
                elif isinstance(msg, SystemMessage):
                    # System messages are informational, we can log them if needed
                    pass

            if not assistant_messages:
                # Check if there was an error
                if result_message and result_message.is_error:
                    raise ClaudeCLIProcessError(
                        f"Claude CLI returned error: {result_message.result or 'Unknown error'}"
                    )
                raise ClaudeCLIProcessError("No assistant message received from Claude CLI")

            # Convert the last assistant message to ModelResponse
            # (in multi-turn conversations, there might be multiple)
            last_assistant_message = assistant_messages[-1]
            model_response = convert_from_claude_message(last_assistant_message, self._model_name)

            # Add usage information if available
            if result_message:
                try:
                    usage = extract_usage_from_result(
                        {
                            "usage": result_message.usage,
                            "duration_ms": result_message.duration_ms,
                            "duration_api_ms": result_message.duration_api_ms,
                            "num_turns": result_message.num_turns,
                            "total_cost_usd": result_message.total_cost_usd,
                        }
                    )
                    # Replace the default usage with extracted one
                    model_response = ModelResponse(
                        parts=model_response.parts,
                        usage=usage,
                        model_name=model_response.model_name,
                        timestamp=model_response.timestamp,
                        provider_name=model_response.provider_name,
                        finish_reason="stop" if not result_message.is_error else "error",
                    )
                except Exception:
                    # If usage extraction fails, continue with default usage
                    pass

            return model_response

        except Exception as e:
            # Wrap any Claude SDK exceptions
            if "CLI not found" in str(e) or "claude: command not found" in str(e):
                raise ClaudeCLINotFoundError() from e
            raise ClaudeCLIProcessError(f"Failed to query Claude CLI: {e}") from e
