"""Logfire + カスタムツールの統合例

このスクリプトは、カスタムツールを使用しながらLogfireで
すべての実行をトレースする方法を示します。

前提条件：
    1. logfireパッケージ: pip install logfire
    2. Logfireアカウント: https://logfire.pydantic.dev/
    3. 認証: logfire auth
    4. プロジェクト: logfire projects new

実行方法：
    uv run python examples/logfire_with_custom_tools.py

Note:
    send_to_logfire=Falseにすると、実際の送信なしでテストできます。
"""

import asyncio

try:
    import logfire
except ImportError:
    print("❌ logfireパッケージがインストールされていません")
    print("   インストール: pip install logfire")
    exit(1)

from pydantic import BaseModel
from pydantic_ai import Agent

from pydantic_claude_cli import ClaudeCodeCLIModel


class Product(BaseModel):
    """商品モデル"""

    name: str
    price: float
    quantity: int = 1


async def main() -> None:
    """Logfire + カスタムツールの例を実行"""

    print("=" * 70)
    print("Logfire + カスタムツール統合例")
    print("=" * 70)
    print()

    # Logfire設定
    print("Logfireを設定中...")
    logfire.configure(send_to_logfire=True)  # テストモード
    logfire.instrument_pydantic_ai()
    print("✓ Logfireインストルメンテーション有効化")
    print()

    # モデルとAgent
    model = ClaudeCodeCLIModel("claude-sonnet-4-5-20250929")
    agent = Agent(
        model, instructions="ツールを使って計算してください。日本語で回答してください。"
    )

    # toolsets設定
    model.set_agent_toolsets(agent._function_toolset)
    print("✓ カスタムツール設定完了")
    print()

    # カスタムツール定義
    @agent.tool_plain
    def calculate_subtotal(items: list[Product]) -> float:
        """商品リストの小計を計算

        Args:
            items: 商品リスト

        Returns:
            小計金額
        """
        total = sum(item.price * item.quantity for item in items)

        # ツール内でもLogfireを使用可能
        logfire.info("calculate_subtotal called", item_count=len(items), total=total)

        return total

    @agent.tool_plain
    def apply_discount(amount: float, discount_rate: float = 0.1) -> float:
        """割引を適用

        Args:
            amount: 金額
            discount_rate: 割引率（デフォルト: 0.1 = 10%）

        Returns:
            割引後の金額
        """
        discounted = amount * (1 - discount_rate)

        logfire.info(
            "apply_discount called",
            amount=amount,
            discount_rate=discount_rate,
            result=discounted,
        )

        return discounted

    @agent.tool_plain
    def format_price(amount: float) -> str:
        """金額をフォーマット

        Args:
            amount: 金額

        Returns:
            フォーマットされた文字列
        """
        formatted = f"¥{amount:,.0f}"

        logfire.debug("format_price called", amount=amount, formatted=formatted)

        return formatted

    print("✓ 3つのカスタムツールを定義:")
    print("    - calculate_subtotal")
    print("    - apply_discount")
    print("    - format_price")
    print()

    # テスト実行
    print("=" * 70)
    print("テスト実行")
    print("=" * 70)
    print()

    # テスト1: 小計計算
    print("【テスト1】商品合計の計算")
    print("質問: 「リンゴ100円×3個、バナナ150円×2個の合計を計算して」")
    print()

    result1 = await agent.run("リンゴ100円×3個、バナナ150円×2個の合計を計算して")
    print(f"回答: {result1.output}")
    print()
    print("-" * 70)
    print()

    # テスト2: 割引適用
    print("【テスト2】割引計算")
    print("質問: 「600円に10%の割引を適用して」")
    print()

    result2 = await agent.run("600円に10%の割引を適用して")
    print(f"回答: {result2.output}")
    print()
    print("-" * 70)
    print()

    # テスト3: 複数ツールの連携
    print("【テスト3】複数ツールの連携")
    print("質問: 「1000円に20%割引を適用して、フォーマットして表示」")
    print()

    result3 = await agent.run("1000円に20%割引を適用して、フォーマットして表示して")
    print(f"回答: {result3.output}")
    print()
    print("-" * 70)
    print()

    # Logfire情報
    print("=" * 70)
    print("Logfire トレース情報")
    print("=" * 70)
    print()
    print("Logfireダッシュボードで確認できる内容：")
    print()
    print("📊 スパン構造：")
    print("  agent run")
    print("  ├─ chat (model request)")
    print("  │  └─ tool execution: calculate_subtotal")
    print("  ├─ chat (model request)")
    print("  │  └─ tool execution: apply_discount")
    print("  └─ chat (final response)")
    print()
    print("📈 メトリクス：")
    print("  - 各ツールの実行時間")
    print("  - トークン使用量")
    print("  - エラー率")
    print("  - レイテンシ分布")
    print()
    print("🔍 属性：")
    print("  - gen_ai.system: claude-code-cli")
    print("  - gen_ai.model: claude-sonnet-4-5-20250929")
    print("  - gen_ai.tool.name: calculate_subtotal, apply_discount, etc.")
    print("  - gen_ai.tool.call.arguments: {...}")
    print("  - gen_ai.tool.call.result: {...}")
    print()

    print("=" * 70)
    print("✅ すべての例が正常に実行されました！")
    print("=" * 70)
    print()
    print("📝 次のステップ:")
    print("  1. send_to_logfire=True に変更して実際に送信")
    print("  2. Logfireダッシュボードでトレースを確認")
    print("     https://logfire.pydantic.dev/")
    print("  3. パフォーマンスの分析とボトルネックの特定")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n中断されました")
    except Exception as e:
        print(f"\n\n❌ エラー: {e}")
        import traceback

        traceback.print_exc()
