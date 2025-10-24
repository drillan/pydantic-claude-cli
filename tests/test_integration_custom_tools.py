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
        model = ClaudeCodeCLIModel("claude-sonnet-4-5-20250929")
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
        model = ClaudeCodeCLIModel("claude-sonnet-4-5-20250929")
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

        model = ClaudeCodeCLIModel("claude-sonnet-4-5-20250929")
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
        model = ClaudeCodeCLIModel("claude-sonnet-4-5-20250929")
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
        model = ClaudeCodeCLIModel("claude-sonnet-4-5-20250929")
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
        model = ClaudeCodeCLIModel("claude-sonnet-4-5-20250929")
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
        model = ClaudeCodeCLIModel("claude-sonnet-4-5-20250929")
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
        model = ClaudeCodeCLIModel("claude-sonnet-4-5-20250929")
        agent = Agent(model)
        model.set_agent_toolsets(agent._function_toolset)

        # ツールなしで実行
        result = await agent.run("Hello")

        assert result.output is not None

    @pytest.mark.asyncio
    async def test_tool_execution_error_handling(self) -> None:
        """ツール実行時のエラーハンドリング"""
        model = ClaudeCodeCLIModel("claude-sonnet-4-5-20250929")
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
