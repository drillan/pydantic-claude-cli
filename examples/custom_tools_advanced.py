"""カスタムツールの高度な使用例

このスクリプトは、Pydanticモデルを使った複雑なツールや
非同期ツールの使い方を示します。

実行方法:
    uv run python examples/custom_tools_advanced.py
"""

import asyncio

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel


class Product(BaseModel):
    """商品モデル"""

    name: str
    price: float
    quantity: int = 1


class Invoice(BaseModel):
    """請求書モデル"""

    items: list[Product]
    tax_rate: float = 0.1


async def main() -> None:
    """高度なカスタムツール例を実行"""

    print("=" * 60)
    print("カスタムツール高度な例 - Pydanticモデルと非同期処理")
    print("=" * 60)
    print()

    # モデルを作成
    model = ClaudeCodeCLIModel("claude-sonnet-4-5-20250929")
    agent = Agent(
        model,
        instructions="ツールを使って商品の計算と処理を行ってください。日本語で回答してください。",
    )

    # 重要: Agent作成後にtoolsetsを設定
    model.set_agent_toolsets(agent._function_toolset)

    # ツール1: 商品合計計算（Pydanticモデル使用）
    @agent.tool_plain
    def calculate_subtotal(items: list[Product]) -> float:
        """商品リストの小計を計算する

        Args:
            items: 商品リスト

        Returns:
            小計金額
        """
        total = sum(item.price * item.quantity for item in items)
        print(f"  [Tool] calculate_subtotal: {len(items)}個の商品 → ¥{total:,.0f}")
        return total

    # ツール2: 税込み金額計算
    @agent.tool_plain
    def calculate_total_with_tax(subtotal: float, tax_rate: float = 0.1) -> float:
        """税込み金額を計算する

        Args:
            subtotal: 小計
            tax_rate: 税率（デフォルト: 0.1 = 10%）

        Returns:
            税込み金額
        """
        total = subtotal * (1 + tax_rate)
        print(
            f"  [Tool] calculate_total_with_tax: ¥{subtotal:,.0f} × {1 + tax_rate} → ¥{total:,.0f}"
        )
        return total

    # ツール3: 請求書生成（複雑なPydanticモデル）
    @agent.tool_plain
    def generate_invoice_summary(invoice: Invoice) -> str:
        """請求書のサマリーを生成する

        Args:
            invoice: 請求書データ

        Returns:
            フォーマットされたサマリー
        """
        print(f"  [Tool] generate_invoice_summary: {len(invoice.items)}個の商品")

        lines = ["【請求書】"]
        for item in invoice.items:
            lines.append(f"  - {item.name}: ¥{item.price:,.0f} × {item.quantity}")

        subtotal = sum(item.price * item.quantity for item in invoice.items)
        tax = subtotal * invoice.tax_rate
        total = subtotal + tax

        lines.append(f"\n小計: ¥{subtotal:,.0f}")
        lines.append(f"消費税({invoice.tax_rate * 100:.0f}%): ¥{tax:,.0f}")
        lines.append(f"合計: ¥{total:,.0f}")

        return "\n".join(lines)

    # ツール4: 非同期データ処理
    @agent.tool_plain
    async def async_validate_products(product_names: list[str]) -> str:
        """商品名を非同期で検証する（シミュレーション）

        Args:
            product_names: 商品名リスト

        Returns:
            検証結果
        """
        print(
            f"  [Tool] async_validate_products: {len(product_names)}個の商品を検証中..."
        )

        # 非同期処理をシミュレート
        await asyncio.sleep(0.1)

        # すべて有効と判定
        validated = [f"✓ {name}" for name in product_names]
        result = "\n".join(validated)

        print("  [Tool] 検証完了: すべて有効")
        return result

    # 例1: Pydanticモデルを使った計算
    print("【例1】Pydanticモデルを使った商品計算")
    print(
        "質問: 「リンゴ（100円×3個）、バナナ（150円×2個）の合計金額を計算してください」"
    )
    print()

    result1 = await agent.run(
        "リンゴ（100円×3個）、バナナ（150円×2個）の合計金額を計算してください"
    )
    print(f"回答: {result1.output}")
    print()
    print("-" * 60)
    print()

    # 例2: 税込み金額計算
    print("【例2】税込み金額計算")
    print("質問: 「600円の10%の税込み金額を計算してください」")
    print()

    result2 = await agent.run("600円の10%の税込み金額を計算してください")
    print(f"回答: {result2.output}")
    print()
    print("-" * 60)
    print()

    # 例3: 複雑な請求書処理
    print("【例3】請求書サマリー生成")
    print("質問: 「以下の商品で請求書を作成してください")
    print("       - ノートPC: 80,000円")
    print("       - マウス: 2,000円 × 2個")
    print("       - キーボード: 5,000円」")
    print()

    result3 = await agent.run(
        "以下の商品で請求書を作成してください：\n"
        "- ノートPC: 80,000円\n"
        "- マウス: 2,000円 × 2個\n"
        "- キーボード: 5,000円"
    )
    print(f"回答:\n{result3.output}")
    print()
    print("-" * 60)
    print()

    # 例4: 非同期ツール
    print("【例4】非同期ツールの使用")
    print("質問: 「リンゴ、バナナ、オレンジの3つの商品を検証してください」")
    print()

    result4 = await agent.run("リンゴ、バナナ、オレンジの3つの商品を検証してください")
    print(f"回答:\n{result4.output}")
    print()
    print("-" * 60)
    print()

    # 使用状況
    print("【使用状況】")
    usage = result4.usage()
    print(f"入力トークン: {usage.request_tokens:,}")
    print(f"出力トークン: {usage.response_tokens:,}")
    print(f"合計トークン: {usage.total_tokens:,}")
    print()

    print("=" * 60)
    print("✅ すべての例が正常に実行されました！")
    print("=" * 60)
    print()
    print("📝 Note:")
    print("  - Phase 1では依存性なしツール（@agent.tool_plain）のみサポート")
    print("  - RunContext依存ツール（@agent.tool）は未サポート")
    print("  - 詳細は docs/custom-tools-explained.md を参照")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n中断されました")
    except Exception as e:
        print(f"\n\n❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
