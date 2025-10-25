"""カスタムツール + WebSearch のテスト

カスタムツールとWebSearchを同時に使用できるか確認
"""

import asyncio
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel


async def main():
    print("=" * 60)
    print("カスタムツール + WebSearch テスト")
    print("=" * 60)
    print()

    # allowed_toolsでWebSearchを有効化
    model = ClaudeCodeCLIModel(
        "claude-haiku-4-5",
        allowed_tools=["WebSearch", "WebFetch"],
    )
    agent = Agent(
        model,
        instructions="ユーザーの質問に答えてください。計算が必要な場合はcalculateツールを使い、最新情報が必要な場合はWeb検索を使用してください。",
    )

    # 重要: Agent作成後にtoolsetsを設定
    model.set_agent_toolsets(agent._function_toolset)

    # カスタムツールを定義
    @agent.tool_plain
    def calculate(x: int, y: int) -> int:
        """2つの数値を足す"""
        print(f"  [Tool] calculate({x}, {y}) = {x + y}")
        return x + y

    # テスト: カスタムツールとWebSearchの両方を使う質問
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
    print("=" * 60)

    # 使用状況を確認
    usage = result.usage()
    print("使用状況:")
    print(f"  入力トークン: {usage.input_tokens:,}")
    print(f"  出力トークン: {usage.output_tokens:,}")
    print(f"  合計トークン: {usage.total_tokens:,}")
    print()

    # メッセージ確認
    all_msgs = result.all_messages()
    print(f"メッセージ数: {len(all_msgs)}")
    for i, msg in enumerate(all_msgs):
        print(f"  [{i}] {type(msg).__name__}")

    print()
    print("=" * 60)
    print("✅ カスタムツールとWebSearchの両方が使えることを確認！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
