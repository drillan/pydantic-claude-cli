"""テスト: deps_context モジュール（Milestone 3）

Article 3 (テストファースト) に従って、実装前にテストを作成。
"""

import asyncio

import pytest


class TestDepsContext:
    """ContextVarによる依存性管理のテスト"""

    def test_set_and_get_deps(self) -> None:
        """依存性の設定と取得"""
        from pydantic_claude_cli.deps_context import (
            get_current_deps,
            get_current_deps_with_type,
            reset_deps,
            set_current_deps,
        )

        # 最初はNone
        assert get_current_deps() is None

        # 設定
        deps = {"api_key": "test123", "count": 42}
        token = set_current_deps(deps, deps_type=dict)

        # 取得（依存性のみ）
        assert get_current_deps() == deps

        # 取得（型情報も含む）
        result = get_current_deps_with_type()
        assert result is not None
        deps_retrieved, deps_type_retrieved = result
        assert deps_retrieved == deps
        assert deps_type_retrieved is dict

        # リセット
        reset_deps(token)
        assert get_current_deps() is None

    def test_nested_deps_context(self) -> None:
        """ネストしたContextVar"""
        from pydantic_claude_cli.deps_context import (
            get_current_deps,
            reset_deps,
            set_current_deps,
        )

        deps1 = {"key": "value1"}
        deps2 = {"key": "value2"}

        # 最初の設定
        token1 = set_current_deps(deps1)
        assert get_current_deps() == deps1

        # 上書き
        token2 = set_current_deps(deps2)
        assert get_current_deps() == deps2

        # 2つ目をリセット
        reset_deps(token2)
        assert get_current_deps() == deps1

        # 1つ目もリセット
        reset_deps(token1)
        assert get_current_deps() is None

    def test_get_deps_without_set(self) -> None:
        """set_current_deps()せずに取得した場合"""
        from pydantic_claude_cli.deps_context import get_current_deps

        # Noneが返る（エラーにならない）
        assert get_current_deps() is None

    @pytest.mark.asyncio
    async def test_async_context_isolation(self) -> None:
        """非同期タスク間でのContextVar分離"""
        from pydantic_claude_cli.deps_context import (
            get_current_deps,
            reset_deps,
            set_current_deps,
        )

        async def task_with_deps(value: str) -> str:
            """依存性を設定してタスクを実行"""
            token = set_current_deps({"value": value})
            try:
                # 他のタスクと並行実行
                await asyncio.sleep(0.01)

                # 自分のタスクの依存性を取得
                deps = get_current_deps()
                assert deps is not None
                assert deps["value"] == value

                return deps["value"]
            finally:
                reset_deps(token)

        # 複数のタスクを並行実行
        results = await asyncio.gather(
            task_with_deps("task1"), task_with_deps("task2"), task_with_deps("task3")
        )

        # それぞれのタスクで正しい依存性が取得された
        assert results == ["task1", "task2", "task3"]

    def test_deps_cleanup_in_exception(self) -> None:
        """例外が発生してもリセットされる"""
        from pydantic_claude_cli.deps_context import (
            get_current_deps,
            reset_deps,
            set_current_deps,
        )

        deps = {"key": "value"}
        token = set_current_deps(deps)

        try:
            # 例外を発生させる
            raise ValueError("test error")
        except ValueError:
            pass
        finally:
            # finallyでリセット
            reset_deps(token)

        # リセットされている
        assert get_current_deps() is None

    def test_multiple_sets_without_reset(self) -> None:
        """reset()せずに複数回set()した場合"""
        from pydantic_claude_cli.deps_context import (
            get_current_deps,
            reset_deps,
            set_current_deps,
        )

        # 1回目
        token1 = set_current_deps({"value": 1})
        assert get_current_deps() == {"value": 1}

        # 2回目（reset()せずに）
        token2 = set_current_deps({"value": 2})
        assert get_current_deps() == {"value": 2}

        # token2をリセット
        reset_deps(token2)
        assert get_current_deps() == {"value": 1}

        # token1をリセット
        reset_deps(token1)
        assert get_current_deps() is None

    def test_deps_with_none(self) -> None:
        """Noneを明示的に設定"""
        from pydantic_claude_cli.deps_context import (
            get_current_deps,
            reset_deps,
            set_current_deps,
        )

        # Noneを設定
        token = set_current_deps(None)

        # Noneが取得される
        assert get_current_deps() is None

        reset_deps(token)

    def test_deps_with_various_types(self) -> None:
        """様々な型の依存性"""
        from pydantic_claude_cli.deps_context import (
            get_current_deps,
            reset_deps,
            set_current_deps,
        )

        # dict
        token1 = set_current_deps({"key": "value"})
        assert get_current_deps() == {"key": "value"}
        reset_deps(token1)

        # list
        token2 = set_current_deps([1, 2, 3])
        assert get_current_deps() == [1, 2, 3]
        reset_deps(token2)

        # str
        token3 = set_current_deps("test_string")
        assert get_current_deps() == "test_string"
        reset_deps(token3)

        # int
        token4 = set_current_deps(42)
        assert get_current_deps() == 42
        reset_deps(token4)
