"""Phase 2/3の動作テスト

BuiltinToolsとToolPresetの動作確認
"""

import asyncio
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel, BuiltinTools, ToolPreset


async def test_builtin_tools():
    """Phase 2: BuiltinTools定数のテスト"""
    print("=" * 60)
    print("Phase 2: BuiltinTools定数テスト")
    print("=" * 60)
    print()

    # BuiltinTools.WEB_TOOLSを使用
    model = ClaudeCodeCLIModel(
        "claude-haiku-4-5",
        allowed_tools=BuiltinTools.WEB_TOOLS,
    )
    agent = Agent(model)

    print("質問: 2025年10月25日時点で、日本の内閣総理大臣を教えてください")
    print()

    result = await agent.run("2025年10月25日時点で、日本の内閣総理大臣を教えてください")

    print("回答:")
    print(result.output)
    print()
    print("✅ BuiltinTools.WEB_TOOLSが正常に動作！")
    print()


async def test_tool_preset():
    """Phase 3: ToolPresetのテスト"""
    print("=" * 60)
    print("Phase 3: ToolPresetテスト")
    print("=" * 60)
    print()

    # ToolPreset.WEB_ENABLEDを使用
    model = ClaudeCodeCLIModel(
        "claude-haiku-4-5",
        tool_preset=ToolPreset.WEB_ENABLED,
    )
    agent = Agent(model)

    print("質問: 2025年10月25日時点で、日本の内閣総理大臣を教えてください")
    print()

    result = await agent.run("2025年10月25日時点で、日本の内閣総理大臣を教えてください")

    print("回答:")
    print(result.output)
    print()
    print("✅ ToolPreset.WEB_ENABLEDが正常に動作！")
    print()


async def test_preset_with_custom_tools():
    """Phase 3: ToolPreset + カスタムツールのテスト"""
    print("=" * 60)
    print("Phase 3: ToolPreset + カスタムツールテスト")
    print("=" * 60)
    print()

    # ToolPreset.WEB_ENABLED + カスタムツール
    model = ClaudeCodeCLIModel(
        "claude-haiku-4-5",
        tool_preset=ToolPreset.WEB_ENABLED,
    )
    agent = Agent(model)
    model.set_agent_toolsets(agent._function_toolset)

    @agent.tool_plain
    def calculate(x: int, y: int) -> int:
        """2つの数値を足す"""
        print(f"  [Tool] calculate({x}, {y}) = {x + y}")
        return x + y

    print(
        "質問: 100+200を計算して、その後2025年10月25日時点の日本の首相を教えてください"
    )
    print()

    result = await agent.run(
        "100+200を計算して、その後2025年10月25日時点の日本の首相を教えてください"
    )

    print("回答:")
    print(result.output)
    print()
    print("✅ ToolPreset + カスタムツールが正常に動作！")
    print()


async def main():
    """すべてのテストを実行"""
    await test_builtin_tools()
    await test_tool_preset()
    await test_preset_with_custom_tools()

    print("=" * 60)
    print("✅ Phase 2/3のすべてのテストが成功！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
