"""BuiltinToolsを使ったツール制御の例

このスクリプトは、BuiltinTools定数を使って組み込みツールを柔軟に制御する方法を示します。

実行方法:
    uv run python examples/websearch_with_builtin_tools.py
"""

import asyncio

from pydantic_ai import Agent

from pydantic_claude_cli import BuiltinTools, ClaudeCodeCLIModel


async def main() -> None:
    """BuiltinToolsを使ったツール制御例を実行"""

    print("=" * 60)
    print("BuiltinToolsを使ったツール制御例")
    print("=" * 60)
    print()

    # BuiltinTools.WEB_TOOLSでWebSearch + WebFetchを有効化
    # Note: Sonnetモデルを推奨（Haikuはツール使用判断が弱い）
    model = ClaudeCodeCLIModel(
        "claude-sonnet-4-5-20250929",
        allowed_tools=BuiltinTools.WEB_TOOLS,
        permission_mode="acceptEdits",  # ツール使用を自動承認
    )

    agent = Agent(
        model,
        instructions="Web検索ツールを使って最新情報を取得してください。知識カットオフ以降の情報が必要な場合は必ずWebSearchを使用してください。",
    )

    print("質問: 2025年10月25日時点で、日本の内閣総理大臣を教えてください")
    print()

    result = await agent.run("2025年10月25日時点で、日本の内閣総理大臣を教えてください")

    print("回答:")
    print(result.output)
    print()
    print("=" * 60)

    # 使用状況を確認
    usage = result.usage()
    print("使用状況:")
    print(f"  入力トークン: {usage.input_tokens:,}")
    print(f"  出力トークン: {usage.output_tokens:,}")
    print(f"  合計トークン: {usage.total_tokens:,}")
    print()

    print("✅ BuiltinTools.WEB_TOOLSでWebSearchが使えました！")
    print()
    print("利用可能な定数:")
    print(f"  - BuiltinTools.WEB_TOOLS: {BuiltinTools.WEB_TOOLS}")
    print(f"  - BuiltinTools.FILE_READ_TOOLS: {BuiltinTools.FILE_READ_TOOLS}")
    print(f"  - BuiltinTools.FILE_WRITE_TOOLS: {BuiltinTools.FILE_WRITE_TOOLS}")
    print(f"  - BuiltinTools.FILE_TOOLS: {BuiltinTools.FILE_TOOLS}")
    print(f"  - BuiltinTools.CODE_TOOLS: {BuiltinTools.CODE_TOOLS}")
    print()
    print("組み合わせ例:")
    print("  model = ClaudeCodeCLIModel(")
    print("      'model-name',")
    print("      allowed_tools=BuiltinTools.WEB_TOOLS + BuiltinTools.FILE_READ_TOOLS")
    print("  )")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n中断されました")
    except Exception as e:
        print(f"\n\n❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
