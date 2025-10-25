"""実験的依存性サポートの高度な使用例（Milestone 3）

このスクリプトは、Pydanticモデル、dataclass、接続の再作成パターンを示します。

Warning:
    これは実験的機能です。シリアライズ可能な依存性のみサポートします。

実行方法:
    uv run python examples/experimental_deps_advanced.py
"""

import asyncio
from dataclasses import dataclass

from pydantic import BaseModel
from pydantic_ai import RunContext
from pydantic_claude_cli import ClaudeCodeCLIAgent, ClaudeCodeCLIModel


# Pydanticモデルの依存性
class ApiConfig(BaseModel):
    """API設定"""

    base_url: str
    api_key: str
    timeout: int = 30
    retries: int = 3


# dataclassの依存性
@dataclass
class DatabaseConfig:
    """データベース設定"""

    db_url: str
    pool_size: int = 10
    echo: bool = False


async def main() -> None:
    """高度な依存性サポート例を実行"""

    print("=" * 60)
    print("実験的依存性サポート - 高度な例（Milestone 3）")
    print("=" * 60)
    print()

    # ===================================================================
    # 例1: Pydanticモデルの依存性
    # ===================================================================

    print("【例1】Pydanticモデルの依存性")
    print()

    model1 = ClaudeCodeCLIModel("claude-haiku-4-5", enable_experimental_deps=True)
    agent1 = ClaudeCodeCLIAgent(
        model1,
        deps_type=ApiConfig,
        system_prompt="ツールを使って設定情報を取得してください。日本語で回答してください。",
    )
    model1.set_agent_toolsets(agent1._function_toolset)

    @agent1.tool
    async def get_api_endpoint(ctx: RunContext[ApiConfig], path: str) -> str:
        """APIエンドポイントを構築する

        Args:
            ctx: RunContext（ApiConfigにアクセス可能）
            path: APIパス

        Returns:
            完全なURL
        """
        url = f"{ctx.deps.base_url}/{path}"
        print(f"  [Tool] get_api_endpoint: {url}")
        print(f"         API Key: {ctx.deps.api_key[:3]}... (masked)")
        print(f"         Timeout: {ctx.deps.timeout}秒")
        return url

    @agent1.tool
    async def check_api_config(ctx: RunContext[ApiConfig]) -> str:
        """API設定を確認する

        Args:
            ctx: RunContext（ApiConfigにアクセス可能）

        Returns:
            設定サマリー
        """
        config_summary = (
            f"Base URL: {ctx.deps.base_url}\n"
            f"Timeout: {ctx.deps.timeout}秒\n"
            f"Retries: {ctx.deps.retries}回\n"
            f"API Key: {ctx.deps.api_key[:3]}... (masked)"
        )
        print("  [Tool] check_api_config:")
        print(f"         {config_summary.replace(chr(10), chr(10) + '         ')}")
        return config_summary

    print("質問: 「/users/123 のエンドポイントURLを教えてください」")
    print()

    result1 = await agent1.run(
        "/users/123 のエンドポイントURLを教えてください",
        deps=ApiConfig(base_url="https://api.example.com", api_key="secret_abc123xyz"),
    )
    print(f"回答: {result1.output}")
    print()
    print("-" * 60)
    print()

    # ===================================================================
    # 例2: dataclassの依存性
    # ===================================================================

    print("【例2】dataclassの依存性")
    print()

    model2 = ClaudeCodeCLIModel("claude-haiku-4-5", enable_experimental_deps=True)
    agent2 = ClaudeCodeCLIAgent(
        model2,
        deps_type=DatabaseConfig,
        system_prompt="ツールを使ってデータベース設定を確認してください。日本語で回答してください。",
    )
    model2.set_agent_toolsets(agent2._function_toolset)

    @agent2.tool
    async def get_db_connection_info(ctx: RunContext[DatabaseConfig]) -> str:
        """データベース接続情報を取得する

        Args:
            ctx: RunContext（DatabaseConfigにアクセス可能）

        Returns:
            接続情報サマリー
        """
        info = (
            f"Database URL: {ctx.deps.db_url}\n"
            f"Pool Size: {ctx.deps.pool_size}\n"
            f"Echo SQL: {ctx.deps.echo}"
        )
        print("  [Tool] get_db_connection_info:")
        print(f"         {info.replace(chr(10), chr(10) + '         ')}")
        return info

    @agent2.tool
    async def simulate_db_query(ctx: RunContext[DatabaseConfig], table: str) -> str:
        """データベースクエリをシミュレートする

        Args:
            ctx: RunContext（DatabaseConfigにアクセス可能）
            table: テーブル名

        Returns:
            クエリ結果（シミュレーション）

        Note:
            実際のデータベース接続はツール内で再作成します。
            依存性には接続文字列と設定のみを含めます。
        """
        db_url = ctx.deps.db_url
        pool_size = ctx.deps.pool_size

        print("  [Tool] simulate_db_query:")
        print(f"         Table: {table}")
        print(f"         DB: {db_url}")
        print(f"         Pool: {pool_size}")

        # 実際にはここでデータベース接続を再作成
        # engine = create_engine(ctx.deps.db_url)
        # with engine.connect() as conn:
        #     result = conn.execute(...)

        # シミュレーション
        return f"Query results from {table} (simulated)"

    print("質問: 「usersテーブルからデータを取得してください」")
    print()

    result2 = await agent2.run(
        "usersテーブルからデータを取得してください",
        deps=DatabaseConfig(db_url="postgresql://localhost/mydb", pool_size=20),
    )
    print(f"回答: {result2.output}")
    print()
    print("-" * 60)
    print()

    # ===================================================================
    # 例3: 複雑なPydanticモデル（ネストした設定）
    # ===================================================================

    print("【例3】ネストしたPydanticモデル")
    print()

    class AuthConfig(BaseModel):
        """認証設定"""

        username: str
        password: str
        token: str | None = None

    class ServiceConfig(BaseModel):
        """サービス設定"""

        service_name: str
        api_url: str
        auth: AuthConfig
        debug: bool = False

    model3 = ClaudeCodeCLIModel("claude-haiku-4-5", enable_experimental_deps=True)
    agent3 = ClaudeCodeCLIAgent(
        model3,
        deps_type=ServiceConfig,
        system_prompt="ツールを使ってサービス設定を確認してください。日本語で回答してください。",
    )
    model3.set_agent_toolsets(agent3._function_toolset)

    @agent3.tool
    async def get_service_info(ctx: RunContext[ServiceConfig]) -> str:
        """サービス情報を取得する

        Args:
            ctx: RunContext（ServiceConfigにアクセス可能）

        Returns:
            サービス情報
        """
        info = (
            f"Service: {ctx.deps.service_name}\n"
            f"API URL: {ctx.deps.api_url}\n"
            f"Username: {ctx.deps.auth.username}\n"
            f"Debug Mode: {ctx.deps.debug}"
        )
        print("  [Tool] get_service_info:")
        print(f"         {info.replace(chr(10), chr(10) + '         ')}")
        return info

    @agent3.tool
    async def authenticate(ctx: RunContext[ServiceConfig]) -> str:
        """認証を実行する（シミュレーション）

        Args:
            ctx: RunContext（ServiceConfigにアクセス可能）

        Returns:
            認証結果
        """
        username = ctx.deps.auth.username
        has_token = ctx.deps.auth.token is not None

        print("  [Tool] authenticate:")
        print(f"         Username: {username}")
        print(f"         Has Token: {has_token}")

        # 認証処理のシミュレーション
        if has_token:
            return f"Authenticated with token for user {username}"
        else:
            return f"Authenticated with password for user {username}"

    print("質問: 「サービスに接続して認証してください」")
    print()

    result3 = await agent3.run(
        "サービスに接続して認証してください",
        deps=ServiceConfig(
            service_name="MyApp",
            api_url="https://myapp.example.com",
            auth=AuthConfig(username="admin", password="secret123", token="token_xyz"),
            debug=True,
        ),
    )
    print(f"回答: {result3.output}")
    print()
    print("-" * 60)
    print()

    # 使用状況
    print("【合計使用状況】")
    total_usage = result1.usage() + result2.usage() + result3.usage()
    print(f"合計入力トークン: {total_usage.input_tokens:,}")
    print(f"合計出力トークン: {total_usage.output_tokens:,}")
    print(f"合計トークン: {total_usage.total_tokens:,}")
    print()

    print("=" * 60)
    print("✅ すべての高度な例が正常に実行されました！")
    print("=" * 60)
    print()
    print("📝 重要なポイント:")
    print("  1. Pydanticモデル、dataclass両方の依存性をサポート")
    print("  2. ネストした設定も正しくシリアライズされる")
    print("  3. 接続オブジェクトは含めず、設定のみを渡す")
    print("  4. ツール内で必要な接続を再作成する")
    print()
    print("⚠️ 制限事項:")
    print("  - httpx.AsyncClient、sqlalchemy.Engine等は非サポート")
    print("  - ctx.retry()、ctx.run_step等は未サポート")
    print("  - 完全なサポートが必要な場合は、AnthropicModelを使用")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n中断されました")
    except Exception as e:
        print(f"\n\n❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
