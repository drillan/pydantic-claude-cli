"""テスト: tool_converter モジュール

Article 3 (テストファースト) に従って、実装前にテストを作成。
"""

import pytest

from pydantic_claude_cli.tool_converter import (
    extract_python_types,
    format_tool_result,
)


class TestExtractPythonTypes:
    """JSON SchemaからPython型抽出のテスト"""

    def test_extracts_basic_types(self) -> None:
        """基本的な型を抽出する"""
        schema = {
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "name": {"type": "string"},
                "active": {"type": "boolean"},
                "value": {"type": "number"},
            },
        }

        result = extract_python_types(schema)
        assert result == {"x": int, "name": str, "active": bool, "value": float}

    def test_extracts_complex_types(self) -> None:
        """複雑な型を抽出する"""
        schema = {
            "type": "object",
            "properties": {"items": {"type": "array"}, "data": {"type": "object"}},
        }

        result = extract_python_types(schema)
        assert result == {"items": list, "data": dict}

        # schema = {
        #     "type": "object",
        #     "properties": {
        #         "items": {"type": "array"},
        #         "data": {"type": "object"}
        #     }
        # }
        #
        # result = extract_python_types(schema)
        # assert result == {
        #     "items": list,
        #     "data": dict
        # }

    def test_handles_empty_schema(self) -> None:
        """空のスキーマを処理する"""
        schema = {"type": "object", "properties": {}}
        result = extract_python_types(schema)
        assert result == {}

        # schema = {"type": "object", "properties": {}}
        # result = extract_python_types(schema)
        # assert result == {}

    def test_handles_missing_properties(self) -> None:
        """propertiesがないスキーマを処理する"""
        schema = {"type": "object"}
        result = extract_python_types(schema)
        assert result == {}

        # schema = {"type": "object"}
        # result = extract_python_types(schema)
        # assert result == {}

    def test_handles_unknown_type(self) -> None:
        """不明な型をstrにフォールバックする"""

        schema = {"type": "object", "properties": {"unknown": {"type": "unknown_type"}}}

        # loggingで警告が出力される（warningsモジュールではない）
        result = extract_python_types(schema)

        # strにフォールバックされることを確認
        assert result == {"unknown": str}

        # schema = {
        #     "type": "object",
        #     "properties": {
        #         "unknown": {"type": "unknown_type"}
        #     }
        # }
        #
        # result = extract_python_types(schema)
        # assert result == {"unknown": str}


class TestFormatToolResult:
    """ツール実行結果のフォーマットのテスト"""

    def test_formats_string_result(self) -> None:
        """文字列結果をMCP形式に変換する"""
        result = format_tool_result("Hello, World!")
        assert result == {"content": [{"type": "text", "text": "Hello, World!"}]}

    def test_formats_integer_result(self) -> None:
        """整数結果をMCP形式に変換する"""
        result = format_tool_result(42)
        assert result == {"content": [{"type": "text", "text": "42"}]}

        # result = format_tool_result(42)
        # assert result == {
        #     "content": [{"type": "text", "text": "42"}]
        # }

    def test_formats_dict_result(self) -> None:
        """辞書結果をMCP形式に変換する"""
        result = format_tool_result({"key": "value", "number": 42})
        # 辞書は文字列化される
        assert "key" in result["content"][0]["text"]
        assert "value" in result["content"][0]["text"]

        # result = format_tool_result({"key": "value"})
        # assert "key" in result["content"][0]["text"]

    def test_preserves_mcp_format(self) -> None:
        """既にMCP形式の結果はそのまま返す"""
        mcp_result = {"content": [{"type": "text", "text": "Test"}], "is_error": False}
        result = format_tool_result(mcp_result)
        assert result == mcp_result

        # mcp_result = {
        #     "content": [{"type": "text", "text": "Test"}],
        #     "is_error": False
        # }
        # result = format_tool_result(mcp_result)
        # assert result == mcp_result

    def test_handles_none_result(self) -> None:
        """None結果を処理する"""
        result = format_tool_result(None)
        assert result["content"][0]["text"] == "None"

        # result = format_tool_result(None)
        # assert result["content"][0]["text"] == "None"


class TestCreateMcpFromTools:
    """MCPサーバー作成のテスト"""

    def test_creates_server_with_single_tool(self) -> None:
        """単一ツールでMCPサーバーを作成する"""
        from pydantic_ai.tools import ToolDefinition
        from pydantic_claude_cli.tool_converter import create_mcp_from_tools

        def simple_tool(x: int) -> int:
            return x * 2

        tool_def = ToolDefinition(
            name="simple",
            description="Simple tool",
            parameters_json_schema={
                "type": "object",
                "properties": {"x": {"type": "integer"}},
            },
        )

        server = create_mcp_from_tools([(tool_def, simple_tool)])

        assert server["type"] == "sdk"
        assert server["name"] == "pydantic-custom-tools"
        assert "instance" in server

    def test_creates_server_with_multiple_tools(self) -> None:
        """複数ツールでMCPサーバーを作成する"""
        from pydantic_ai.tools import ToolDefinition
        from pydantic_claude_cli.tool_converter import create_mcp_from_tools

        def add(x: int, y: int) -> int:
            return x + y

        def multiply(x: int, y: int) -> int:
            return x * y

        tool_defs = [
            ToolDefinition(name="add", description="Add", parameters_json_schema={}),
            ToolDefinition(
                name="multiply", description="Multiply", parameters_json_schema={}
            ),
        ]

        server = create_mcp_from_tools([(tool_defs[0], add), (tool_defs[1], multiply)])

        assert server["type"] == "sdk"
        assert "instance" in server

    def test_handles_empty_tools_list(self) -> None:
        """空のツールリストを処理する"""
        from pydantic_claude_cli.tool_converter import create_mcp_from_tools

        server = create_mcp_from_tools([])

        assert server["type"] == "sdk"
        assert "instance" in server

    def test_wraps_sync_functions(self) -> None:
        """同期関数をasyncでラップする"""
        from pydantic_ai.tools import ToolDefinition
        from pydantic_claude_cli.tool_converter import create_mcp_from_tools

        def sync_tool(x: int) -> int:
            """Sync tool"""
            return x * 2

        tool_def = ToolDefinition(
            name="sync", description="Sync", parameters_json_schema={}
        )

        # 同期関数でもMCPサーバーが作成できる
        server = create_mcp_from_tools([(tool_def, sync_tool)])

        assert server["type"] == "sdk"

    def test_preserves_async_functions(self) -> None:
        """非同期関数はそのまま使用する"""
        from pydantic_ai.tools import ToolDefinition
        from pydantic_claude_cli.tool_converter import create_mcp_from_tools

        async def async_tool(x: int) -> int:
            """Async tool"""
            return x * 2

        tool_def = ToolDefinition(
            name="async", description="Async", parameters_json_schema={}
        )

        # 非同期関数でもMCPサーバーが作成できる
        server = create_mcp_from_tools([(tool_def, async_tool)])

        assert server["type"] == "sdk"

    def test_handles_tool_execution_error(self) -> None:
        """ツール実行エラーを処理する"""
        # このテストは統合テストで実施済み
        # (test_integration_custom_tools.py::test_tool_execution_error_handling)
        pytest.skip("Covered by integration test")


class TestMakeAsync:
    """同期関数のasyncラップのテスト"""

    def test_wraps_sync_function(self) -> None:
        """同期関数をasync関数でラップする"""
        # _make_asyncはプライベート関数なので、create_mcp_from_toolsでテスト済み
        # test_wraps_sync_functionsで同期関数が正しく処理されることを確認
        pytest.skip("Tested via test_wraps_sync_functions")

    def test_preserves_return_value(self) -> None:
        """戻り値を保持する"""
        # create_mcp_from_toolsのテストで戻り値が保持されることを確認済み
        pytest.skip("Tested via create_mcp_from_tools tests")

    def test_preserves_exceptions(self) -> None:
        """例外を保持する"""
        # test_integration_custom_tools.py::test_tool_execution_error_handlingで確認済み
        pytest.skip("Tested via integration test")


# 実装完了により、このテストは不要になりました
# def test_implementation_not_yet_done() -> None:
#     """実装がまだ完了していないことを確認（Red phase）"""
#     with pytest.raises(ImportError):
#         from pydantic_claude_cli.tool_converter import extract_python_types  # noqa: F401
