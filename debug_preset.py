"""ToolPresetのデバッグ"""

import asyncio
from pydantic_claude_cli import ClaudeCodeCLIModel, ToolPreset


async def main():
    model = ClaudeCodeCLIModel("claude-haiku-4-5", tool_preset=ToolPreset.WEB_ENABLED)

    # 内部状態を確認
    print(f"tool_preset: {model._tool_preset}")
    print(f"allowed_tools: {model._allowed_tools}")
    print(f"disallowed_tools: {model._disallowed_tools}")
    print()

    # _resolve_toolsの結果を確認
    allowed, disallowed = model._resolve_tools([])
    print("_resolve_tools([])の結果:")
    print(f"  allowed: {allowed}")
    print(f"  disallowed: {disallowed}")
    print()

    # プリセットから取得されるツール
    preset = ToolPreset.WEB_ENABLED
    print(f"ToolPreset.WEB_ENABLED.get_allowed_tools(): {preset.get_allowed_tools()}")


if __name__ == "__main__":
    asyncio.run(main())
