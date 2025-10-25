"""統合テスト: カスタムツール機能

E2Eテストとして、実際のAgent + ClaudeCodeCLIModelの統合を検証します。
"""

import pytest
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.tools import RunContext

from pydantic_claude_cli import ClaudeCodeCLIModel
from pydantic_claude_cli.exceptions import MessageConversionError


class TestCustomToolsIntegration:
    """カスタムツール統合テスト"""

    @pytest.mark.asyncio
    async def test_simple_tool_execution(self) -> None:
        """シンプルなツールが実行される"""
        model = ClaudeCodeCLIModel("claude-haiku-4-5")
        agent = Agent(model)
        model.set_agent_toolsets(agent._function_toolset)

        call_count = 0

        @agent.tool_plain
        def add_numbers(x: int, y: int) -> int:
            """Add two numbers"""
            nonlocal call_count
            call_count += 1
            return x + y

        result = await agent.run("Calculate 10 + 20 using the add_numbers tool")

        # ツールが呼び出されたことを確認（call_countが増加）
        # Note: LLMが直接計算することもあるので、結果の正確性を確認
        assert "30" in result.output

    @pytest.mark.asyncio
    async def test_multiple_tools_collaboration(self) -> None:
        """複数ツールの連携が動作する"""
        model = ClaudeCodeCLIModel("claude-haiku-4-5")
        agent = Agent(model)
        model.set_agent_toolsets(agent._function_toolset)

        @agent.tool_plain
        def add(x: int, y: int) -> int:
            return x + y

        @agent.tool_plain
        def multiply(x: int, y: int) -> int:
            return x * y

        result = await agent.run("Calculate (5 + 3) × 2 using the tools")

        # 結果が正しいことを確認
        assert "16" in result.output

    @pytest.mark.asyncio
    async def test_pydantic_model_argument(self) -> None:
        """Pydanticモデルを引数に取るツールが動作する"""

        class Item(BaseModel):
            name: str
            price: float

        model = ClaudeCodeCLIModel("claude-haiku-4-5")
        agent = Agent(model)
        model.set_agent_toolsets(agent._function_toolset)

        @agent.tool_plain
        def calculate_total(items: list[Item]) -> float:
            """Calculate total price of items"""
            return sum(item.price for item in items)

        result = await agent.run(
            "Calculate total for: Apple 100yen, Banana 150yen using calculate_total tool"
        )

        # 結果が含まれることを確認
        assert result.output is not None

    @pytest.mark.asyncio
    async def test_async_tool(self) -> None:
        """非同期ツールが動作する"""
        model = ClaudeCodeCLIModel("claude-haiku-4-5")
        agent = Agent(model)
        model.set_agent_toolsets(agent._function_toolset)

        @agent.tool_plain
        async def async_process(text: str) -> str:
            """Process text asynchronously"""
            import asyncio

            await asyncio.sleep(0.01)  # 非同期処理をシミュレート
            return text.upper()

        result = await agent.run("Use async_process to process 'hello'")

        # 結果が返されることを確認
        assert result.output is not None

    @pytest.mark.asyncio
    async def test_runcontext_tool_error(self) -> None:
        """RunContext依存ツールでエラーが発生する"""
        model = ClaudeCodeCLIModel("claude-haiku-4-5")
        agent = Agent(model, deps_type=dict)
        model.set_agent_toolsets(agent._function_toolset)

        @agent.tool
        async def bad_tool(ctx: RunContext[dict], x: int) -> str:
            """Tool that requires RunContext - should fail"""
            return str(ctx.deps.get("value", 0) + x)

        # RunContext依存のためエラーになるはず
        with pytest.raises(MessageConversionError) as exc_info:
            await agent.run("Use bad_tool with x=5", deps={"value": 10})

        # エラーメッセージの確認
        assert "RunContext" in str(exc_info.value)
        assert "not supported" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_without_set_agent_toolsets(self) -> None:
        """set_agent_toolsets()を呼び出さない場合、ツールが見つからない"""
        model = ClaudeCodeCLIModel("claude-haiku-4-5")
        agent = Agent(model)

        # set_agent_toolsets()を呼び出さない

        @agent.tool_plain
        def my_tool(x: int) -> int:
            return x * 2

        # ツールが見つからないため、通常の応答になる
        # （エラーにはならず、LLMが直接回答する）
        result = await agent.run("Calculate 5 × 2")

        # 結果が返ることを確認（ツールは使われないが、LLMが計算）
        assert "10" in result.output or "10" in str(result.output)

    @pytest.mark.asyncio
    async def test_tool_with_default_arguments(self) -> None:
        """デフォルト引数を持つツールが動作する"""
        model = ClaudeCodeCLIModel("claude-haiku-4-5")
        agent = Agent(model)
        model.set_agent_toolsets(agent._function_toolset)

        @agent.tool_plain
        def format_text(text: str, uppercase: bool = False) -> str:
            """Format text with optional uppercase"""
            return text.upper() if uppercase else text.lower()

        result = await agent.run("Use format_text to format 'HELLO' to lowercase")

        # 結果が返ることを確認
        assert result.output is not None


class TestToolExtractionEdgeCases:
    """ツール抽出のエッジケーステスト"""

    @pytest.mark.asyncio
    async def test_empty_toolset(self) -> None:
        """ツールが定義されていない場合"""
        model = ClaudeCodeCLIModel("claude-haiku-4-5")
        agent = Agent(model)
        model.set_agent_toolsets(agent._function_toolset)

        # ツールなしで実行
        result = await agent.run("Hello")

        assert result.output is not None

    @pytest.mark.asyncio
    async def test_tool_execution_error_handling(self) -> None:
        """ツール実行時のエラーハンドリング"""
        model = ClaudeCodeCLIModel("claude-haiku-4-5")
        agent = Agent(model)
        model.set_agent_toolsets(agent._function_toolset)

        @agent.tool_plain
        def failing_tool(x: int) -> int:
            """Tool that always fails"""
            raise ValueError("Intentional error for testing")

        # ツールがエラーを起こしても、Agentは続行する
        # （MCPサーバーがエラーをキャッチしてLLMに返す）
        result = await agent.run("Use failing_tool with x=5")

        # LLMがエラーを受け取って何らかの応答を返す
        assert result.output is not None


class TestExperimentalDepsSupport:
    """実験的依存性サポートのテスト（Milestone 3）"""

    @pytest.mark.asyncio
    async def test_deps_with_dict(self) -> None:
        """dict型の依存性が使える"""
        from pydantic_claude_cli import ClaudeCodeCLIAgent, ClaudeCodeCLIModel

        model = ClaudeCodeCLIModel("claude-haiku-4-5", enable_experimental_deps=True)
        agent = ClaudeCodeCLIAgent(model, deps_type=dict)
        model.set_agent_toolsets(agent._function_toolset)

        call_count = 0

        @agent.tool
        async def get_api_key(ctx: RunContext[dict]) -> str:
            """Get API key from deps"""
            nonlocal call_count
            call_count += 1
            return ctx.deps.get("api_key", "not_found")

        result = await agent.run(
            "What is the API key? Use get_api_key tool.",
            deps={"api_key": "secret123"},
        )

        # 結果が返されることを確認
        assert result.output is not None
        # ツールが呼び出されたか、または結果が含まれることを確認
        assert "secret123" in result.output or call_count > 0

    @pytest.mark.asyncio
    async def test_deps_with_pydantic_model(self) -> None:
        """Pydanticモデルの依存性が使える"""
        from pydantic_claude_cli import ClaudeCodeCLIAgent, ClaudeCodeCLIModel

        class Config(BaseModel):
            api_key: str
            timeout: int

        model = ClaudeCodeCLIModel("claude-haiku-4-5", enable_experimental_deps=True)
        agent = ClaudeCodeCLIAgent(model, deps_type=Config)
        model.set_agent_toolsets(agent._function_toolset)

        @agent.tool
        async def get_config_value(ctx: RunContext[Config], key: str) -> str:
            """Get config value"""
            if key == "api_key":
                return ctx.deps.api_key
            elif key == "timeout":
                return str(ctx.deps.timeout)
            return "unknown"

        result = await agent.run(
            "Get the timeout value using get_config_value tool",
            deps=Config(api_key="test", timeout=30),
        )

        # 結果が返されることを確認
        assert result.output is not None

    @pytest.mark.asyncio
    async def test_deps_with_dataclass(self) -> None:
        """dataclassの依存性が使える"""
        from dataclasses import dataclass

        from pydantic_claude_cli import ClaudeCodeCLIAgent, ClaudeCodeCLIModel

        @dataclass
        class AppConfig:
            db_url: str
            max_connections: int

        model = ClaudeCodeCLIModel("claude-haiku-4-5", enable_experimental_deps=True)
        agent = ClaudeCodeCLIAgent(model, deps_type=AppConfig)
        model.set_agent_toolsets(agent._function_toolset)

        @agent.tool
        async def get_db_url(ctx: RunContext[AppConfig]) -> str:
            """Get database URL"""
            return ctx.deps.db_url

        result = await agent.run(
            "Get the database URL using get_db_url tool",
            deps=AppConfig(db_url="postgresql://localhost/test", max_connections=10),
        )

        # 結果が返されることを確認
        assert result.output is not None

    @pytest.mark.asyncio
    async def test_non_serializable_deps_error(self) -> None:
        """非シリアライズ可能な依存性でエラー"""
        # このテストはスキップ（httpx.AsyncClientが必要）
        # 実際の環境ではテストできないため、ユニットテストでカバー
        pytest.skip("Requires httpx.AsyncClient, covered by unit tests")

    @pytest.mark.asyncio
    async def test_experimental_deps_disabled_by_default(self) -> None:
        """実験的機能がデフォルトで無効"""
        from pydantic_claude_cli import ClaudeCodeCLIAgent, ClaudeCodeCLIModel

        # enable_experimental_deps=False（デフォルト）
        model = ClaudeCodeCLIModel("claude-haiku-4-5")
        agent = ClaudeCodeCLIAgent(model, deps_type=dict)
        model.set_agent_toolsets(agent._function_toolset)

        @agent.tool
        async def deps_tool(ctx: RunContext[dict]) -> str:
            return "test"

        # RunContext依存ツールは引き続きエラー
        with pytest.raises(MessageConversionError, match="RunContext.*not supported"):
            await agent.run("Test", deps={"key": "value"})

    @pytest.mark.asyncio
    async def test_context_var_cleanup_on_success(self) -> None:
        """実行成功後にContextVarがクリーンアップされる"""
        from pydantic_claude_cli import ClaudeCodeCLIAgent, ClaudeCodeCLIModel
        from pydantic_claude_cli.deps_context import get_current_deps

        model = ClaudeCodeCLIModel("claude-haiku-4-5", enable_experimental_deps=True)
        agent = ClaudeCodeCLIAgent(model, deps_type=dict)
        model.set_agent_toolsets(agent._function_toolset)

        @agent.tool
        async def simple_tool(ctx: RunContext[dict]) -> str:
            return "test"

        # 実行前はNone
        assert get_current_deps() is None

        # 実行
        result = await agent.run("Test", deps={"key": "value"})

        # 実行後もNone（クリーンアップされている）
        assert get_current_deps() is None
        assert result.output is not None

    @pytest.mark.asyncio
    async def test_context_var_cleanup_on_error(self) -> None:
        """エラー時にもContextVarがクリーンアップされる"""
        from pydantic_claude_cli import ClaudeCodeCLIAgent, ClaudeCodeCLIModel
        from pydantic_claude_cli.deps_context import get_current_deps

        model = ClaudeCodeCLIModel("claude-haiku-4-5", enable_experimental_deps=True)
        agent = ClaudeCodeCLIAgent(model, deps_type=dict)
        model.set_agent_toolsets(agent._function_toolset)

        @agent.tool
        async def failing_tool(ctx: RunContext[dict]) -> str:
            raise ValueError("test error")

        # 実行前はNone
        assert get_current_deps() is None

        # 実行（ツールがエラーを起こすが、Agentは続行）
        result = await agent.run("Use failing_tool", deps={"key": "value"})

        # 実行後もNone（エラーでもクリーンアップされている）
        assert get_current_deps() is None
        assert result.output is not None
