"""ClaudeCodeCLIModel用のAgentラッパー（実験的依存性サポート）

このクラスは、Pydantic AIのAgentを継承し、
依存性をContextVarに設定/クリーンアップします。

Milestone 3の一部として実装されました。

Warning:
    これは実験的機能です。シリアライズ可能な依存性のみサポートします。

Example:
    ```python
    from pydantic_ai import RunContext
    from pydantic_claude_cli import ClaudeCodeCLIModel, ClaudeCodeCLIAgent

    model = ClaudeCodeCLIModel('claude-sonnet-4-5-20250929')
    agent = ClaudeCodeCLIAgent(model, deps_type=dict)
    model.set_agent_toolsets(agent._function_toolset)

    @agent.tool
    async def get_user(ctx: RunContext[dict], user_id: int) -> str:
        api_key = ctx.deps.get("api_key")
        # API keyを使ってユーザー情報を取得
        return f"User {user_id}"

    result = await agent.run("Get user 123", deps={"api_key": "abc"})
    ```
"""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic_ai import Agent

from .deps_context import reset_deps, set_current_deps

__all__ = ("ClaudeCodeCLIAgent",)

# 型パラメータ
AgentDepsT = TypeVar("AgentDepsT")


class ClaudeCodeCLIAgent(Agent[AgentDepsT]):  # type: ignore[misc]
    """ClaudeCodeCLIModel用のAgentラッパー（実験的依存性サポート）

    このクラスは、依存性をContextVarに設定し、
    ClaudeCodeCLIModel.request()で取得できるようにします。

    Warning:
        これは実験的機能です。シリアライズ可能な依存性のみサポートします。

    Example:
        >>> from pydantic_claude_cli import ClaudeCodeCLIModel, ClaudeCodeCLIAgent
        >>> model = ClaudeCodeCLIModel('claude-sonnet-4-5-20250929')
        >>> agent = ClaudeCodeCLIAgent(model, deps_type=dict)
        >>> model.set_agent_toolsets(agent._function_toolset)
        >>> # ツールを定義
        >>> @agent.tool_plain
        ... def my_tool(x: int) -> int:
        ...     return x * 2
        >>> # 実行（実際のLLM呼び出しが必要）
        >>> # result = await agent.run("Calculate 5 × 2")  # doctest: +SKIP

    Note:
        完全なRunContextサポートが必要な場合は、Pydantic AI標準
        （AnthropicModel）を使用してください。
    """

    async def run(self, *args: Any, deps: Any = None, **kwargs: Any) -> Any:
        """Agentを実行し、depsをContextVarに設定する

        Args:
            *args: Agent.run()の位置引数
            deps: 依存性（シリアライズ可能な型のみ）
            **kwargs: Agent.run()のキーワード引数

        Returns:
            Agent.run()の戻り値

        Note:
            depsはContextVarに設定され、ClaudeCodeCLIModel.request()で
            取得されます。実行後は自動的にクリーンアップされます。

        Example:
            >>> from pydantic_claude_cli import ClaudeCodeCLIModel, ClaudeCodeCLIAgent
            >>> model = ClaudeCodeCLIModel('test')
            >>> agent = ClaudeCodeCLIAgent(model, deps_type=dict)
            >>> # result = await agent.run("Hello", deps={"key": "value"})  # doctest: +SKIP
        """
        # depsをContextVarに設定（型情報も一緒に）
        token = None
        if deps is not None:
            # Agent._deps_type属性から型情報を取得
            deps_type = getattr(self, "_deps_type", None)
            token = set_current_deps(deps, deps_type=deps_type)

        try:
            # 通常のAgent.run()を呼び出し
            return await super().run(*args, deps=deps, **kwargs)
        finally:
            # クリーンアップ
            if token is not None:
                reset_deps(token)

    def run_sync(self, *args: Any, deps: Any = None, **kwargs: Any) -> Any:
        """Agentを同期実行し、depsをContextVarに設定する

        Args:
            *args: Agent.run_sync()の位置引数
            deps: 依存性（シリアライズ可能な型のみ）
            **kwargs: Agent.run_sync()のキーワード引数

        Returns:
            Agent.run_sync()の戻り値

        Note:
            depsはContextVarに設定され、ClaudeCodeCLIModel.request()で
            取得されます。実行後は自動的にクリーンアップされます。

        Example:
            >>> from pydantic_claude_cli import ClaudeCodeCLIModel, ClaudeCodeCLIAgent
            >>> model = ClaudeCodeCLIModel('test')
            >>> agent = ClaudeCodeCLIAgent(model, deps_type=dict)
            >>> # result = agent.run_sync("Hello", deps={"key": "value"})  # doctest: +SKIP
        """
        # depsをContextVarに設定（型情報も一緒に）
        token = None
        if deps is not None:
            # Agent._deps_type属性から型情報を取得
            deps_type = getattr(self, "_deps_type", None)
            token = set_current_deps(deps, deps_type=deps_type)

        try:
            # 通常のAgent.run_sync()を呼び出し
            return super().run_sync(*args, deps=deps, **kwargs)
        finally:
            # クリーンアップ
            if token is not None:
                reset_deps(token)
