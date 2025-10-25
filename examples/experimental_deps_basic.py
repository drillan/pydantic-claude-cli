"""実験的依存性サポートの基本的な使用例（Milestone 3）

このスクリプトは、ClaudeCodeCLIAgentとdictを使った
シンプルな依存性注入の使い方を示します。

Warning:
    これは実験的機能です。シリアライズ可能な依存性のみサポートします。

実行方法:
    uv run python examples/experimental_deps_basic.py
"""

import asyncio

from pydantic_ai import RunContext
from pydantic_claude_cli import ClaudeCodeCLIAgent, ClaudeCodeCLIModel


async def main() -> None:
    """基本的な依存性サポート例を実行"""

    print("=" * 60)
    print("実験的依存性サポート - 基本例（Milestone 3）")
    print("=" * 60)
    print()

    # ステップ1: モデルを作成（実験的機能を有効化）
    print("【ステップ1】モデル作成")
    model = ClaudeCodeCLIModel(
        "claude-sonnet-4-5-20250929",
        enable_experimental_deps=True,  # 実験的機能
    )
    print("  ✅ ClaudeCodeCLIModel作成完了（enable_experimental_deps=True）")
    print()

    # ステップ2: ClaudeCodeCLIAgentを使用（重要！）
    print("【ステップ2】ClaudeCodeCLIAgent作成")
    agent = ClaudeCodeCLIAgent(
        model,
        deps_type=dict,  # 依存性の型を指定
        system_prompt="ツールを使って質問に答えてください。日本語で回答してください。",
    )
    model.set_agent_toolsets(agent._function_toolset)
    print("  ✅ ClaudeCodeCLIAgent作成完了（deps_type=dict）")
    print()

    # ステップ3: RunContext依存ツールを定義
    print("【ステップ3】RunContext依存ツールを定義")

    # ツール1: 設定値を取得
    @agent.tool
    async def get_config(ctx: RunContext[dict], key: str) -> str:
        """設定値を取得する

        Args:
            ctx: RunContext（depsにアクセス可能）
            key: 設定キー

        Returns:
            設定値
        """
        value = ctx.deps.get(key, "not found")
        print(f"  [Tool] get_config: key='{key}' → '{value}'")
        return str(value)

    # ツール2: APIキーを検証
    @agent.tool
    async def validate_api_key(ctx: RunContext[dict]) -> str:
        """APIキーを検証する

        Args:
            ctx: RunContext（depsにアクセス可能）

        Returns:
            検証結果
        """
        api_key = ctx.deps.get("api_key", "")
        print(f"  [Tool] validate_api_key: key='{api_key[:3]}...' (masked)")

        # 簡易検証
        if len(api_key) < 10:
            return "Invalid: API key too short"

        return f"Valid: API key starts with '{api_key[:3]}...'"

    # ツール3: 複数の設定値を組み合わせる
    @agent.tool
    async def build_endpoint_url(ctx: RunContext[dict], path: str) -> str:
        """エンドポイントURLを構築する

        Args:
            ctx: RunContext（depsにアクセス可能）
            path: APIパス

        Returns:
            完全なURL
        """
        base_url = ctx.deps.get("base_url", "https://api.example.com")
        version = ctx.deps.get("api_version", "v1")

        url = f"{base_url}/{version}/{path}"
        print(f"  [Tool] build_endpoint_url: path='{path}' → '{url}'")
        return url

    print("  ✅ 3つのツールを定義完了")
    print()

    # ステップ4: 実行（depsを渡す）
    print("【ステップ4】実行（depsを渡す）")
    print()

    # 依存性を定義
    app_deps = {
        "api_key": "secret_abc123xyz",
        "base_url": "https://api.example.com",
        "api_version": "v2",
        "timeout": 30,
        "max_retries": 3,
    }

    print("依存性:")
    print(f"  - api_key: {app_deps['api_key'][:3]}... (masked)")
    print(f"  - base_url: {app_deps['base_url']}")
    print(f"  - api_version: {app_deps['api_version']}")
    print(f"  - timeout: {app_deps['timeout']}")
    print(f"  - max_retries: {app_deps['max_retries']}")
    print()

    # 例1: 設定値の取得
    print("-" * 60)
    print("【例1】設定値の取得")
    print("質問: 「タイムアウト値を教えてください」")
    print()

    result1 = await agent.run("タイムアウト値を教えてください", deps=app_deps)
    print(f"回答: {result1.output}")
    print()

    # 例2: APIキーの検証
    print("-" * 60)
    print("【例2】APIキーの検証")
    print("質問: 「APIキーは有効ですか？」")
    print()

    result2 = await agent.run("APIキーは有効ですか？", deps=app_deps)
    print(f"回答: {result2.output}")
    print()

    # 例3: エンドポイントURL構築
    print("-" * 60)
    print("【例3】エンドポイントURL構築")
    print("質問: 「/users/123 のエンドポイントURLを構築してください」")
    print()

    result3 = await agent.run(
        "/users/123 のエンドポイントURLを構築してください", deps=app_deps
    )
    print(f"回答: {result3.output}")
    print()

    # 例4: 複数の設定値を使用
    print("-" * 60)
    print("【例4】複数の設定値を使用")
    print("質問: 「最大リトライ回数とタイムアウトの設定を教えてください」")
    print()

    result4 = await agent.run(
        "最大リトライ回数とタイムアウトの設定を教えてください", deps=app_deps
    )
    print(f"回答: {result4.output}")
    print()

    # 使用状況
    print("-" * 60)
    print("【使用状況】")
    usage = result4.usage()
    print(f"入力トークン: {usage.input_tokens:,}")
    print(f"出力トークン: {usage.output_tokens:,}")
    print(f"合計トークン: {usage.total_tokens:,}")
    print()

    print("=" * 60)
    print("✅ すべての例が正常に実行されました！")
    print("=" * 60)
    print()
    print("📝 Note:")
    print("  - この機能は実験的です（Milestone 3）")
    print("  - シリアライズ可能な依存性のみサポート")
    print("  - 詳細は docs/experimental-deps.md を参照")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n中断されました")
    except Exception as e:
        print(f"\n\n❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
