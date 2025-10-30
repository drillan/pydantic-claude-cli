"""ModelSettings support example.

This example demonstrates how to use ModelSettings to control model behavior.

Note: This is an experimental feature. The settings are passed via extra_args
      to Claude Code CLI, and support depends on the CLI implementation.
"""

from __future__ import annotations

import asyncio

from pydantic_ai import Agent
from pydantic_ai.models import ModelSettings

from pydantic_claude_cli import ClaudeCodeCLIModel


async def example_basic_settings() -> None:
    """Basic ModelSettings usage."""
    print("=== Basic ModelSettings Example ===\n")

    # Create model with settings
    model = ClaudeCodeCLIModel(
        "claude-haiku-4-5",
        settings=ModelSettings(
            temperature=0.7,  # Control randomness (0.0 = deterministic, 1.0 = creative)
            max_tokens=500,  # Limit response length
            top_p=0.9,  # Control diversity
        ),
    )

    agent = Agent(model, instructions="You are a helpful assistant.")

    result = await agent.run("簡単な自己紹介をしてください")
    print(f"Response: {result.output}\n")


async def example_temperature_comparison() -> None:
    """Compare different temperature settings."""
    print("=== Temperature Comparison ===\n")

    prompt = "3つの創造的な物語のタイトルを考えてください"

    # Low temperature (more deterministic)
    print("--- Temperature = 0.2 (Deterministic) ---")
    model_low = ClaudeCodeCLIModel(
        "claude-haiku-4-5", settings=ModelSettings(temperature=0.2)
    )
    agent_low = Agent(model_low)
    result_low = await agent_low.run(prompt)
    print(f"{result_low.output}\n")

    # High temperature (more creative)
    print("--- Temperature = 1.0 (Creative) ---")
    model_high = ClaudeCodeCLIModel(
        "claude-haiku-4-5", settings=ModelSettings(temperature=1.0)
    )
    agent_high = Agent(model_high)
    result_high = await agent_high.run(prompt)
    print(f"{result_high.output}\n")


async def example_max_tokens() -> None:
    """Control response length with max_tokens."""
    print("=== Max Tokens Control ===\n")

    # Short response
    print("--- Max Tokens = 50 ---")
    model_short = ClaudeCodeCLIModel(
        "claude-haiku-4-5", settings=ModelSettings(max_tokens=50)
    )
    agent_short = Agent(model_short)
    result_short = await agent_short.run("人工知能について説明してください")
    print(f"{result_short.output}\n")

    # Longer response
    print("--- Max Tokens = 200 ---")
    model_long = ClaudeCodeCLIModel(
        "claude-haiku-4-5", settings=ModelSettings(max_tokens=200)
    )
    agent_long = Agent(model_long)
    result_long = await agent_long.run("人工知能について説明してください")
    print(f"{result_long.output}\n")


async def example_combined_settings() -> None:
    """Use multiple settings together."""
    print("=== Combined Settings Example ===\n")

    model = ClaudeCodeCLIModel(
        "claude-haiku-4-5",
        settings=ModelSettings(
            temperature=0.8,  # Creative
            max_tokens=300,  # Moderate length
            top_p=0.95,  # High diversity
        ),
    )

    agent = Agent(model, instructions="あなたは詩人です。美しい表現を使ってください。")

    result = await agent.run("春の朝について短い詩を書いてください")
    print(f"Response:\n{result.output}\n")


async def main() -> None:
    """Run all examples."""
    print("ModelSettings Example\n")
    print(
        "Note: This feature is experimental. "
        "Claude Code CLI may not support all parameters.\n"
    )
    print("=" * 60)
    print()

    await example_basic_settings()
    await example_temperature_comparison()
    await example_max_tokens()
    await example_combined_settings()

    print("=" * 60)
    print("\nAll examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
