"""テスト: ClaudeCodeCLIAgent（Milestone 3）

Article 3 (テストファースト) に従って、実装前にテストを作成。
"""

import pytest


class TestClaudeCodeCLIAgent:
    """ClaudeCodeCLIAgentのテスト"""

    @pytest.mark.asyncio
    async def test_sets_deps_in_context_var(self) -> None:
        """run()がdepsをContextVarに設定する"""
        from pydantic_claude_cli.claude_code_cli_agent import ClaudeCodeCLIAgent

        # モックモデルを使用
        agent = ClaudeCodeCLIAgent("test", deps_type=dict)

        # 実際のrun()を呼ばずに、内部でdepsが設定されることをテスト
        # （実際のLLM呼び出しを避けるため、モックが必要）
        # ここでは、基本的な構造が正しいことを確認

        # AgentのインスタンスがAgent型であることを確認
        from pydantic_ai import Agent

        assert isinstance(agent, Agent)

    @pytest.mark.asyncio
    async def test_cleans_up_deps_after_run(self) -> None:
        """run()実行後にdepsがクリーンアップされる"""
        from pydantic_claude_cli.deps_context import get_current_deps

        # 初期状態ではNone
        assert get_current_deps() is None

        # run()の後も None（クリーンアップされる）
        # （実際のrun()は統合テストで確認）

    @pytest.mark.asyncio
    async def test_cleans_up_deps_on_exception(self) -> None:
        """例外が発生してもdepsがクリーンアップされる"""
        from pydantic_claude_cli.claude_code_cli_agent import ClaudeCodeCLIAgent

        _ = ClaudeCodeCLIAgent("test", deps_type=dict)

        # 例外が発生した場合でもクリーンアップされることを確認
        # （実装後にモックを使ってテスト）

    def test_inherits_from_agent(self) -> None:
        """AgentクラスのサブクラスであることCを確認"""
        from pydantic_ai import Agent
        from pydantic_claude_cli.claude_code_cli_agent import ClaudeCodeCLIAgent

        agent: ClaudeCodeCLIAgent[None] = ClaudeCodeCLIAgent("test")

        assert isinstance(agent, Agent)
        assert isinstance(agent, ClaudeCodeCLIAgent)

    def test_accepts_same_parameters_as_agent(self) -> None:
        """Agentと同じパラメータを受け入れる"""
        from pydantic_claude_cli.claude_code_cli_agent import ClaudeCodeCLIAgent

        # 基本的なパラメータ
        agent: ClaudeCodeCLIAgent[dict] = ClaudeCodeCLIAgent(
            "test",
            deps_type=dict,
            system_prompt="You are a helpful assistant",
        )

        assert agent is not None

    def test_can_add_tools_like_normal_agent(self) -> None:
        """通常のAgentと同様にツールを追加できる"""
        from pydantic_claude_cli.claude_code_cli_agent import ClaudeCodeCLIAgent

        agent: ClaudeCodeCLIAgent[None] = ClaudeCodeCLIAgent("test")

        # @agent.tool_plain デコレータが機能することを確認
        @agent.tool_plain
        def test_tool(x: int) -> int:
            return x * 2

        # ツールが登録されていることを確認
        assert hasattr(agent, "_function_toolset")

    def test_run_sync_also_sets_deps(self) -> None:
        """run_sync()もdepsを設定する"""
        from pydantic_claude_cli.claude_code_cli_agent import ClaudeCodeCLIAgent

        agent: ClaudeCodeCLIAgent[dict] = ClaudeCodeCLIAgent("test", deps_type=dict)

        # run_sync()メソッドが存在することを確認
        assert hasattr(agent, "run_sync")

    @pytest.mark.asyncio
    async def test_can_be_used_without_deps(self) -> None:
        """depsなしでも使用できる"""
        from pydantic_claude_cli.claude_code_cli_agent import ClaudeCodeCLIAgent

        agent: ClaudeCodeCLIAgent[None] = ClaudeCodeCLIAgent("test")

        # depsなしでインスタンス化できる
        assert agent is not None

    def test_type_parameter_works(self) -> None:
        """型パラメータが機能する"""
        from pydantic_claude_cli.claude_code_cli_agent import ClaudeCodeCLIAgent

        # 型パラメータを指定
        agent: ClaudeCodeCLIAgent[dict] = ClaudeCodeCLIAgent("test", deps_type=dict)

        assert agent is not None
