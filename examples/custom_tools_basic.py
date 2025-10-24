"""カスタムツールの基本的な使用例

このスクリプトは、pydantic-claude-cli v0.2+で追加されたカスタムツール機能の
基本的な使い方を示します。

Phase 1では依存性なしツール（@agent.tool_plain）のみがサポートされています。

実行方法:
    uv run python examples/custom_tools_basic.py
"""

import asyncio

from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel


async def main() -> None:
    """カスタムツールの基本例を実行"""

    print("=" * 60)
    print("カスタムツール基本例 - Phase 1 (依存性なしツール)")
    print("=" * 60)
    print()

    # モデルを作成
    model = ClaudeCodeCLIModel("claude-sonnet-4-5-20250929")
    agent = Agent(model, instructions="ツールを使って計算してください。")

    # 重要: Agent作成後にtoolsetsを設定
    # これにより、Modelがカスタムツールにアクセスできるようになります
    model.set_agent_toolsets(agent._function_toolset)

    # カスタムツール1: 足し算
    @agent.tool_plain
    def add(x: int, y: int) -> int:
        """2つの数値を足し算する

        Args:
            x: 1つ目の数値
            y: 2つ目の数値

        Returns:
            x + y の結果
        """
        print(f"  [Tool] add({x}, {y}) が呼び出されました")
        return x + y

    # カスタムツール2: 掛け算
    @agent.tool_plain
    def multiply(x: int, y: int) -> int:
        """2つの数値を掛け算する

        Args:
            x: 1つ目の数値
            y: 2つ目の数値

        Returns:
            x * y の結果
        """
        print(f"  [Tool] multiply({x}, {y}) が呼び出されました")
        return x * y

    # カスタムツール3: 文字列フォーマット
    @agent.tool_plain
    def format_currency(amount: float, currency: str = "JPY") -> str:
        """金額を通貨形式でフォーマットする

        Args:
            amount: 金額
            currency: 通貨コード（デフォルト: JPY）

        Returns:
            フォーマットされた文字列
        """
        print(f"  [Tool] format_currency({amount}, {currency}) が呼び出されました")
        return f"{amount:,.0f} {currency}"

    # 例1: 基本的な計算
    print("【例1】基本的な計算")
    print("質問: 「5 + 3を計算してください」")
    print()

    result1 = await agent.run("5 + 3を計算してください")
    print(f"回答: {result1.output}")
    print()
    print("-" * 60)
    print()

    # 例2: 複数ツールの連携
    print("【例2】複数ツールの連携")
    print("質問: 「(10 + 5) × 3 を計算してください」")
    print()

    result2 = await agent.run("(10 + 5) × 3 を計算してください")
    print(f"回答: {result2.output}")
    print()
    print("-" * 60)
    print()

    # 例3: 通貨フォーマット
    print("【例3】通貨フォーマット")
    print("質問: 「100円、200円、300円の合計を計算して、通貨形式で表示してください」")
    print()

    result3 = await agent.run(
        "100円、200円、300円の合計を計算して、通貨形式で表示してください"
    )
    print(f"回答: {result3.output}")
    print()
    print("-" * 60)
    print()

    # 使用状況を表示
    print("【使用状況】")
    usage = result3.usage()
    print(
        f"入力トークン: {usage.input_tokens if hasattr(usage, 'input_tokens') else 'N/A'}"
    )
    print(
        f"出力トークン: {usage.output_tokens if hasattr(usage, 'output_tokens') else 'N/A'}"
    )
    print(f"合計リクエスト: {usage.requests}")
    print()

    print("=" * 60)
    print("✅ すべての例が正常に実行されました！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
