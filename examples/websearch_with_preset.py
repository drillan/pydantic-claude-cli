"""ToolPresetを使ったWeb検索の例

このスクリプトは、ToolPresetを使って組み込みツールを有効化する方法を示します。

実行方法:
    uv run python examples/websearch_with_preset.py
"""

import asyncio

from pydantic_ai import Agent

from pydantic_claude_cli import ClaudeCodeCLIModel, ToolPreset


async def main() -> None:
    """ToolPresetを使ったWeb検索例を実行"""

    print("=" * 60)
    print("ToolPresetを使ったWeb検索例")
    print("=" * 60)
    print()

    # ToolPreset.WEB_ENABLEDでWebSearch + WebFetchを有効化
    # Note: Sonnetモデルを推奨（Haikuはツール使用判断が弱い）
    model = ClaudeCodeCLIModel(
        "claude-sonnet-4-5-20250929",
        tool_preset=ToolPreset.WEB_ENABLED,
        permission_mode="acceptEdits",  # ツール使用を自動承認
    )

    agent = Agent(
        model,
        instructions="Web検索ツールを使って最新情報を取得してください。知識カットオフ以降の情報が必要な場合は必ずWebSearchを使用してください。",
    )

    print("質問: 2025年10月25日時点で、日本の内閣総理大臣を教えてください")
    print()

    result = await agent.run(
        "2025年10月25日時点で、日本の内閣総理大臣を教えてください。"
        "必ずWebSearchツールを使用して最新情報を取得してください。"
    )

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

    print("✅ ToolPreset.WEB_ENABLEDでWebSearchが使えました！")
    print()
    print("利用可能なプリセット:")
    print("  - ToolPreset.WEB_ENABLED: Web検索とコンテンツ取得")
    print("  - ToolPreset.READ_ONLY: ファイル読み込みのみ")
    print("  - ToolPreset.SAFE: 読み込み + Web（Bashなし）")
    print("  - ToolPreset.ALL: すべての組み込みツール")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n中断されました")
    except Exception as e:
        print(f"\n\n❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
