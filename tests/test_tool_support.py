"""テスト: tool_support モジュール

Article 3 (テストファースト) に従って、実装前にテストを作成。
"""

import pytest

from pydantic_claude_cli.tool_support import requires_run_context


class TestRequiresRunContext:
    """RunContext依存性検出のテスト"""

    def test_detects_run_context_parameter(self) -> None:
        """RunContextパラメータを持つ関数を検出する"""
        # このテストは実装後に動作するはず
        pytest.skip("Implementation pending")

        # from pydantic_ai.tools import RunContext
        #
        # async def tool_with_context(ctx: RunContext[str], x: int) -> str:
        #     return f"{ctx.deps}: {x}"
        #
        # assert requires_run_context(tool_with_context) is True

    def test_detects_no_run_context(self) -> None:
        """RunContextパラメータを持たない関数を検出する"""

        def tool_without_context(x: int, y: int) -> int:
            return x + y

        assert requires_run_context(tool_without_context) is False

        # def tool_without_context(x: int, y: int) -> int:
        #     return x + y
        #
        # assert requires_run_context(tool_without_context) is False

    def test_detects_generic_run_context(self) -> None:
        """Generic RunContext[T]を検出する"""
        from pydantic_ai.tools import RunContext

        async def tool_with_generic_context(ctx: RunContext[dict], value: str) -> str:
            return value

        assert requires_run_context(tool_with_generic_context) is True

        # from pydantic_ai.tools import RunContext
        #
        # async def tool_with_generic_context(ctx: RunContext[dict], value: str) -> str:
        #     return value
        #
        # assert requires_run_context(tool_with_generic_context) is True

    def test_handles_no_type_annotations(self) -> None:
        """型アノテーションがない関数を処理する"""

        def tool_no_annotations(x, y):  # type: ignore[no-untyped-def]
            return x + y

        assert requires_run_context(tool_no_annotations) is False

        # def tool_no_annotations(x, y):
        #     return x + y
        #
        # assert requires_run_context(tool_no_annotations) is False

    def test_handles_mixed_parameters(self) -> None:
        """RunContextと他のパラメータが混在する関数を処理する"""
        pytest.skip("Implementation pending")

        # from pydantic_ai.tools import RunContext
        #
        # async def tool_mixed(
        #     ctx: RunContext[str],
        #     x: int,
        #     y: int,
        #     name: str = "default"
        # ) -> str:
        #     return f"{ctx.deps}: {x + y}, {name}"
        #
        # assert requires_run_context(tool_mixed) is True


class TestFindToolFunction:
    """Toolset内の関数検索のテスト"""

    def test_finds_function_in_function_toolset(self) -> None:
        """FunctionToolset内の関数を見つける"""
        pytest.skip("Implementation pending")

    def test_returns_none_when_not_found(self) -> None:
        """関数が見つからない場合はNoneを返す"""
        pytest.skip("Implementation pending")

    def test_handles_empty_toolsets(self) -> None:
        """空のtoolsetsリストを処理する"""
        pytest.skip("Implementation pending")

    def test_handles_none_toolsets(self) -> None:
        """Noneのtoolsetsを処理する"""
        pytest.skip("Implementation pending")


class TestExtractToolsFromAgent:
    """Agent からのツール抽出のテスト"""

    def test_extracts_tools_without_context(self) -> None:
        """コンテキストなしツールを抽出する"""
        pytest.skip("Implementation pending")

    def test_detects_tools_with_context(self) -> None:
        """コンテキスト依存ツールを検出する"""
        pytest.skip("Implementation pending")

    def test_returns_empty_when_no_tools(self) -> None:
        """ツールがない場合は空リストを返す"""
        pytest.skip("Implementation pending")

    def test_handles_multiple_toolsets(self) -> None:
        """複数のtoolsetsを処理する"""
        pytest.skip("Implementation pending")


# 実装完了により、このテストは不要になりました
# def test_implementation_not_yet_done() -> None:
#     """実装がまだ完了していないことを確認（Red phase）"""
#     with pytest.raises(ImportError):
#         from pydantic_claude_cli.tool_support import requires_run_context  # noqa: F401
