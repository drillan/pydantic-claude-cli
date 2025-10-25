"""ToolDefinitionからSDK MCPツールへの変換

このモジュールは、Pydantic AIのToolDefinitionを
claude_code_sdkのMCPツール形式に変換する機能を提供します。

主な機能:
- JSON SchemaからPython型の抽出
- ツール実行結果のMCP形式への変換
- MCPサーバーの作成
"""

from __future__ import annotations

import inspect
import logging
from typing import Any, Callable, cast

from claude_code_sdk import tool as sdk_tool
from claude_code_sdk.types import McpSdkServerConfig
from pydantic_ai.tools import ToolDefinition

from .mcp_server_fixed import create_fixed_sdk_mcp_server

# ロガーを設定
logger = logging.getLogger(__name__)


def extract_python_types(json_schema: dict[str, Any]) -> dict[str, type]:
    """JSON SchemaからPython型マッピングを抽出する

    Args:
        json_schema: JSON Schema dict

    Returns:
        {param_name: python_type} のマッピング

    Example:
        >>> schema = {
        ...     "type": "object",
        ...     "properties": {
        ...         "x": {"type": "integer"},
        ...         "name": {"type": "string"}
        ...     }
        ... }
        >>> extract_python_types(schema)
        {'x': <class 'int'>, 'name': <class 'str'>}
    """
    properties = json_schema.get("properties", {})

    # JSON型からPython型へのマッピング
    type_map: dict[str, type] = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    result: dict[str, type] = {}

    for prop_name, prop_schema in properties.items():
        json_type = prop_schema.get("type", "string")

        if json_type not in type_map:
            # 不明な型の場合は警告してstrにフォールバック
            logger.warning(
                "Unknown JSON type '%s' for parameter '%s', using str as fallback",
                json_type,
                prop_name,
            )
            result[prop_name] = str
        else:
            result[prop_name] = type_map[json_type]

    return result


def format_tool_result(result: Any) -> dict[str, Any]:
    """ツール実行結果をMCP形式に変換する

    Args:
        result: ツールの戻り値

    Returns:
        MCP ToolResult形式のdict

    Example:
        >>> format_tool_result("Hello")
        {'content': [{'type': 'text', 'text': 'Hello'}]}
        >>> format_tool_result(42)
        {'content': [{'type': 'text', 'text': '42'}]}
    """
    # 既にMCP形式の場合はそのまま返す
    if isinstance(result, dict) and "content" in result:
        return result

    # 文字列に変換してMCP形式にする
    text_content = str(result)

    return {"content": [{"type": "text", "text": text_content}]}


def _make_async(func: Callable[..., Any]) -> Callable[..., Any]:
    """同期関数をasync関数でラップする

    Args:
        func: 同期関数

    Returns:
        async関数

    Example:
        >>> def sync_func(x: int) -> int:
        ...     return x * 2
        >>> async_func = _make_async(sync_func)
        >>> import asyncio
        >>> asyncio.run(async_func(5))
        10
    """

    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    return async_wrapper


def create_mcp_from_tools(
    tools_with_funcs: list[tuple[ToolDefinition, Callable[..., Any]]],
    deps_data: str | None = None,
    deps_type: type | None = None,
) -> McpSdkServerConfig:
    """ツールリストからMCPサーバーを作成する（依存性サポート付き）

    Args:
        tools_with_funcs: (ToolDefinition, 実行関数)のペアリスト
        deps_data: シリアライズされた依存性（JSON文字列、Milestone 3）
        deps_type: 依存性の型（デシリアライズに使用）

    Returns:
        McpSdkServerConfig dict

    Example:
        >>> def add(x: int, y: int) -> int:
        ...     return x + y
        >>> tool_def = ToolDefinition(
        ...     name="add",
        ...     description="Add numbers",
        ...     parameters_json_schema={
        ...         "type": "object",
        ...         "properties": {
        ...             "x": {"type": "integer"},
        ...             "y": {"type": "integer"}
        ...         }
        ...     }
        ... )
        >>> server = create_mcp_from_tools([(tool_def, add)])
        >>> # ClaudeCodeOptionsに渡す
        >>> # options = ClaudeCodeOptions(mcp_servers={"custom": server})

    Note:
        Milestone 3: deps_dataが指定されている場合、
        RunContext依存ツールに対してEmulatedRunContextを提供します。
    """
    sdk_tools = []

    for tool_def, func in tools_with_funcs:
        # JSON SchemaからPython型を抽出
        input_schema = extract_python_types(tool_def.parameters_json_schema)

        # 同期関数をasyncでラップ
        if not inspect.iscoroutinefunction(func):
            async_func = _make_async(func)
        else:
            async_func = func

        # RunContext依存性をチェック（Milestone 3）
        from .tool_support import requires_run_context

        needs_context = requires_run_context(func)

        # SDK MCPツールを作成
        # NOTE: Pythonのクロージャの問題を回避するため、
        # デフォルト引数で関数を束縛する
        @sdk_tool(tool_def.name, tool_def.description or "", input_schema)
        async def wrapped(
            args: dict[str, Any],
            _func: Callable[..., Any] = async_func,
            _needs_ctx: bool = needs_context,
            _deps: str | None = deps_data,
            _deps_type: type | None = deps_type,
        ) -> dict[str, Any]:
            """MCPツールのラッパー関数"""
            try:
                # Milestone 3: RunContext依存の場合はエミュレート
                if _needs_ctx and _deps:
                    from .deps_support import deserialize_deps
                    from .emulated_run_context import EmulatedRunContext

                    # 依存性をデシリアライズ（型情報を使用）
                    deps_obj = deserialize_deps(_deps, deps_type=_deps_type)

                    # EmulatedRunContextを作成
                    ctx = EmulatedRunContext(deps=deps_obj)

                    # ctxを渡して関数を実行
                    result = await _func(ctx=ctx, **args)
                else:
                    # 通常のツール（依存性なし）
                    result = await _func(**args)

                # 結果をMCP形式に変換
                return format_tool_result(result)
            except Exception as e:
                # エラーをMCP形式で返す
                logger.error("Tool execution error: %s", e, exc_info=True)
                return {
                    "content": [
                        {"type": "text", "text": f"Tool execution error: {str(e)}"}
                    ],
                    "is_error": True,
                }

        sdk_tools.append(wrapped)

    # MCPサーバー作成
    # NOTE: 修正版create_fixed_sdk_mcp_server()を使用
    # claude-code-sdkの既知のバグ（Issue #6710）を回避
    logger.info(
        "Creating MCP server 'pydantic-custom-tools' with %d tools", len(sdk_tools)
    )

    server = create_fixed_sdk_mcp_server(
        name="pydantic-custom-tools", version="1.0.0", tools=sdk_tools
    )

    logger.info(
        "MCP server created successfully: type=%s, name=%s",
        server.get("type"),
        server.get("name"),
    )

    return cast(McpSdkServerConfig, server)
