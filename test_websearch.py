"""WebSearch機能のテスト

カスタムツールなしでWebSearchが利用可能か確認
"""

import asyncio
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel


async def main():
    print("=" * 60)
    print("WebSearch機能テスト")
    print("=" * 60)
    print()

    # allowed_toolsでWebSearchを有効化
    model = ClaudeCodeCLIModel(
        "claude-haiku-4-5",
        allowed_tools=["WebSearch", "WebFetch"],
    )
    agent = Agent(
        model,
        instructions="ユーザーの質問に答えてください。必要に応じてWeb検索を使用してください。",
    )

    # WebSearchを必要とする質問
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
    print(f"  入力トークン: {usage.request_tokens:,}")
    print(f"  出力トークン: {usage.response_tokens:,}")
    print(f"  合計トークン: {usage.total_tokens:,}")
    print()

    # WebSearchが使われたかメッセージから確認
    all_msgs = result.all_messages()
    print(f"メッセージ数: {len(all_msgs)}")
    for i, msg in enumerate(all_msgs):
        print(f"  [{i}] {type(msg).__name__}")
        if hasattr(msg, "parts"):
            for part in msg.parts:
                print(f"      - {type(part).__name__}")


if __name__ == "__main__":
    asyncio.run(main())
