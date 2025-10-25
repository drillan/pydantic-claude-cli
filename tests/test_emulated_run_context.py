"""テスト: EmulatedRunContext（Milestone 3）

Article 3 (テストファースト) に従って、実装前にテストを作成。
"""

import pytest


class TestEmulatedRunContext:
    """EmulatedRunContextのテスト"""

    def test_access_deps(self) -> None:
        """depsプロパティにアクセスできる"""
        from pydantic_claude_cli.emulated_run_context import EmulatedRunContext

        deps = {"api_key": "test123", "count": 42}
        ctx = EmulatedRunContext(deps=deps)

        assert ctx.deps == deps
        assert ctx.deps["api_key"] == "test123"
        assert ctx.deps["count"] == 42

    def test_deps_with_dict(self) -> None:
        """dict型の依存性"""
        from pydantic_claude_cli.emulated_run_context import EmulatedRunContext

        deps = {"key": "value"}
        ctx = EmulatedRunContext(deps=deps)

        assert ctx.deps["key"] == "value"

    def test_deps_with_custom_object(self) -> None:
        """カスタムオブジェクトの依存性"""
        from pydantic_claude_cli.emulated_run_context import EmulatedRunContext

        class CustomDeps:
            def __init__(self, value: str):
                self.value = value

        deps = CustomDeps("test")
        ctx = EmulatedRunContext(deps=deps)

        assert ctx.deps.value == "test"

    def test_unsupported_property_raises_error(self) -> None:
        """未サポートのプロパティにアクセスするとエラー"""
        from pydantic_claude_cli.emulated_run_context import EmulatedRunContext

        ctx = EmulatedRunContext(deps={"key": "value"})

        # retry プロパティにアクセス
        with pytest.raises(AttributeError, match="has no attribute 'retry'"):
            _ = ctx.retry  # type: ignore[attr-defined]

    def test_unsupported_run_step_raises_error(self) -> None:
        """run_stepプロパティは未サポート"""
        from pydantic_claude_cli.emulated_run_context import EmulatedRunContext

        ctx = EmulatedRunContext(deps={"key": "value"})

        with pytest.raises(AttributeError, match="has no attribute 'run_step'"):
            _ = ctx.run_step  # type: ignore[attr-defined]

    def test_unsupported_usage_raises_error(self) -> None:
        """usageプロパティは未サポート"""
        from pydantic_claude_cli.emulated_run_context import EmulatedRunContext

        ctx = EmulatedRunContext(deps={"key": "value"})

        with pytest.raises(AttributeError, match="has no attribute 'usage'"):
            _ = ctx.usage  # type: ignore[attr-defined]

    def test_error_message_mentions_limitation(self) -> None:
        """エラーメッセージに制限事項が含まれる"""
        from pydantic_claude_cli.emulated_run_context import EmulatedRunContext

        ctx = EmulatedRunContext(deps={"key": "value"})

        with pytest.raises(AttributeError) as exc_info:
            _ = ctx.model  # type: ignore[attr-defined]

        error_msg = str(exc_info.value)
        assert "Only 'deps' is supported" in error_msg
        assert "emulated runcontext" in error_msg.lower()

    def test_error_message_suggests_workaround(self) -> None:
        """エラーメッセージに回避策が含まれる"""
        from pydantic_claude_cli.emulated_run_context import EmulatedRunContext

        ctx = EmulatedRunContext(deps={"key": "value"})

        with pytest.raises(AttributeError) as exc_info:
            _ = ctx.messages  # type: ignore[attr-defined]

        error_msg = str(exc_info.value)
        assert "AnthropicModel" in error_msg or "Pydantic AI standard" in error_msg

    def test_deps_is_readonly(self) -> None:
        """depsは読み取り専用（変更は可能だが推奨されない）"""
        from pydantic_claude_cli.emulated_run_context import EmulatedRunContext

        deps = {"key": "value"}
        ctx = EmulatedRunContext(deps=deps)

        # depsは変更可能（dictを渡しているため）
        ctx.deps["key"] = "new_value"
        assert ctx.deps["key"] == "new_value"

        # 元のdepsも変更される（同じオブジェクトを参照）
        assert deps["key"] == "new_value"

    def test_type_parameter(self) -> None:
        """型パラメータが機能する"""
        from pydantic_claude_cli.emulated_run_context import EmulatedRunContext

        # 型パラメータを指定
        ctx: EmulatedRunContext[dict] = EmulatedRunContext(deps={"key": "value"})

        # depsの型は dict
        assert isinstance(ctx.deps, dict)
