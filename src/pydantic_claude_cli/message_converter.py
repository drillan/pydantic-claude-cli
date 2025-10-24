"""Message format conversion between Pydantic AI and Claude Code SDK."""

from __future__ import annotations

from typing import Any

from claude_code_sdk.types import (
    AssistantMessage,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
)
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    ModelResponsePart,
    SystemPromptPart,
    TextPart,
    ThinkingPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.usage import RequestUsage

from .exceptions import MessageConversionError


def convert_to_claude_prompt(messages: list[ModelRequest | ModelResponse]) -> str:
    """Convert Pydantic AI messages to a Claude SDK prompt.

    This is a simplified conversion for the initial implementation that
    only supports text-based messages. Tool calls and multimodal content
    are not yet supported.

    Args:
        messages: List of Pydantic AI messages to convert.

    Returns:
        A string prompt suitable for Claude SDK.

    Raises:
        MessageConversionError: If message conversion fails.
    """
    prompt_parts: list[str] = []

    for message in messages:
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, SystemPromptPart):
                    # System prompts are handled separately via ClaudeCodeOptions
                    continue
                elif isinstance(part, UserPromptPart):
                    if isinstance(part.content, str):
                        prompt_parts.append(part.content)
                    else:
                        # Multimodal content - not yet supported
                        raise MessageConversionError(
                            "Multimodal content in UserPromptPart is not yet supported"
                        )
                elif isinstance(part, (ToolReturnPart, ToolCallPart)):
                    # Tool-related parts - not yet supported
                    raise MessageConversionError(
                        f"Tool-related message parts are not yet supported: {type(part).__name__}"
                    )
        elif isinstance(message, ModelResponse):
            # Model responses in the history - extract text
            for part in message.parts:
                if isinstance(part, TextPart):
                    prompt_parts.append(f"Assistant: {part.content}")
                elif isinstance(part, ThinkingPart):
                    # Include thinking as context
                    prompt_parts.append(f"[Thinking: {part.content}]")

    return "\n\n".join(prompt_parts)


def extract_system_prompt(messages: list[ModelRequest | ModelResponse]) -> str | None:
    """Extract system prompt from messages.

    Args:
        messages: List of Pydantic AI messages.

    Returns:
        System prompt string if found, None otherwise.
    """
    for message in messages:
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, SystemPromptPart):
                    return part.content
    return None


def convert_from_claude_message(
    message: AssistantMessage, model_name: str | None = None
) -> ModelResponse:
    """Convert Claude SDK AssistantMessage to Pydantic AI ModelResponse.

    Args:
        message: Claude SDK assistant message.
        model_name: Optional model name for the response.

    Returns:
        Pydantic AI ModelResponse.

    Raises:
        MessageConversionError: If message conversion fails.
    """
    parts: list[ModelResponsePart] = []

    for block in message.content:
        if isinstance(block, TextBlock):
            parts.append(TextPart(content=block.text))
        elif isinstance(block, ThinkingBlock):
            parts.append(
                ThinkingPart(
                    content=block.thinking,
                    signature=block.signature,
                    provider_name="claude-code-cli",
                )
            )
        elif isinstance(block, ToolUseBlock):
            # Tool use blocks - convert to ToolCallPart
            parts.append(
                ToolCallPart(
                    tool_name=block.name,
                    args=block.input,
                    tool_call_id=block.id,
                )
            )
        elif isinstance(block, ToolResultBlock):
            # Tool result blocks - convert to ToolReturnPart
            # Note: This is a simplified conversion
            content_str = (
                block.content
                if isinstance(block.content, str)
                else str(block.content)
                if block.content
                else ""
            )
            parts.append(
                ToolReturnPart(
                    tool_name="",  # Tool name not available in ToolResultBlock
                    content=content_str,
                    tool_call_id=block.tool_use_id,
                )
            )
        else:
            raise MessageConversionError(f"Unknown content block type: {type(block)}")

    return ModelResponse(
        parts=parts,
        model_name=model_name or message.model,
        provider_name="claude-code-cli",
    )


def extract_usage_from_result(result_data: dict[str, Any]) -> RequestUsage:
    """Extract usage information from Claude SDK result message.

    Args:
        result_data: Result message data from Claude SDK.

    Returns:
        RequestUsage object with extracted information.
    """
    usage_dict = result_data.get("usage", {})

    # Claude SDK provides usage in Anthropic format
    return RequestUsage(
        request_tokens=usage_dict.get("input_tokens", 0),
        response_tokens=usage_dict.get("output_tokens", 0),
        total_tokens=usage_dict.get("input_tokens", 0)
        + usage_dict.get("output_tokens", 0),
        # Additional details
        details={
            "duration_ms": result_data.get("duration_ms", 0),
            "duration_api_ms": result_data.get("duration_api_ms", 0),
            "num_turns": result_data.get("num_turns", 0),
            "total_cost_usd": result_data.get("total_cost_usd"),
        },
    )
