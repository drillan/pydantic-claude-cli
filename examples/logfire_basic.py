"""Pydantic Logfire基本例

このスクリプトは、pydantic-claude-cliでPydantic Logfireを使用する方法を示します。

前提条件：
    1. logfireパッケージがインストールされている: pip install logfire
    2. Logfireアカウントがある: https://logfire.pydantic.dev/
    3. 認証済み: logfire auth
    4. プロジェクト設定済み: logfire projects new

実行方法：
    uv run python examples/logfire_basic.py

Note:
    send_to_logfire=Falseにすると、実際の送信なしでテストできます。
"""

import asyncio

try:
    import logfire
except ImportError:
    print("❌ logfireパッケージがインストールされていません")
    print("   インストール: pip install logfire")
    print("   または: uv add logfire")
    exit(1)

from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel


async def main() -> None:
    """Logfire基本例を実行"""

    print("=" * 70)
    print("Pydantic Logfire 基本例")
    print("=" * 70)
    print()

    # Logfireを設定
    print("ステップ1: Logfireを設定")
    print()

    # テスト用: 実際には送信しない（send_to_logfire=False）
    # 本番環境では send_to_logfire=True（デフォルト）にする
    logfire.configure(send_to_logfire=False)  # Falseでローカルテスト
    print("  ✓ Logfire設定完了（send_to_logfire=False, テストモード）")
    print()

    # Pydantic AIのインストルメンテーションを有効化
    print("ステップ2: Pydantic AIインストルメンテーションを有効化")
    logfire.instrument_pydantic_ai()
    print("  ✓ インストルメンテーション有効化完了")
    print()

    # モデルとAgentを作成
    print("ステップ3: モデルとAgentを作成")
    model = ClaudeCodeCLIModel("claude-sonnet-4-5-20250929")
    agent = Agent(model, instructions="簡潔に答えてください。")
    print("  ✓ ClaudeCodeCLIModel + Agent作成完了")
    print()

    # 実行
    print("=" * 70)
    print("Agent実行")
    print("=" * 70)
    print()

    print("質問: 「2 + 2は？」")
    print()

    result = await agent.run("2 + 2は？数字だけ答えてください。")

    print(f"回答: {result.output}")
    print()

    # トレース情報
    print("=" * 70)
    print("トレース情報")
    print("=" * 70)
    print()
    print("Logfireダッシュボードで以下が確認できます：")
    print("  - Agent実行のトレース（agent run span）")
    print("  - モデルリクエスト（chat span）")
    print("  - トークン使用量")
    print("  - レイテンシ")
    print()

    # 使用量情報
    usage = result.usage()
    print("使用量:")
    print(f"  - リクエスト: {usage.requests}")
    print(f"  - 入力トークン: {usage.input_tokens if hasattr(usage, 'input_tokens') else 'N/A'}")
    print(f"  - 出力トークン: {usage.output_tokens if hasattr(usage, 'output_tokens') else 'N/A'}")
    print()

    print("=" * 70)
    print("✅ Logfire基本例が正常に実行されました！")
    print("=" * 70)
    print()
    print("📝 Note:")
    print("  - send_to_logfire=False でテストしました")
    print("  - 本番環境では logfire.configure() のみで実際に送信されます")
    print("  - Logfireダッシュボード: https://logfire.pydantic.dev/")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n中断されました")
    except Exception as e:
        print(f"\n\n❌ エラー: {e}")
        import traceback

        traceback.print_exc()
