"""修正版SDK MCPサーバー実装

claude-code-sdkのcreate_sdk_mcp_server()にバグがあるため、
独自の実装を提供します。

この実装は、元のコードをベースに、動作するように修正したものです。
"""

from __future__ import annotations

import logging
from typing import Any

from claude_code_sdk import SdkMcpTool
from claude_code_sdk.types import McpSdkServerConfig
from mcp.server import Server
from mcp.types import TextContent, Tool

# ロガーを設定
logger = logging.getLogger(__name__)


def create_fixed_sdk_mcp_server(
    name: str, version: str = "1.0.0", tools: list[SdkMcpTool[Any]] | None = None
) -> McpSdkServerConfig:
    """修正版SDK MCPサーバーを作成する

    claude-code-sdkのcreate_sdk_mcp_server()のバグを修正した実装です。

    Args:
        name: サーバー名
        version: バージョン
        tools: ツールリスト

    Returns:
        McpSdkServerConfig

    Note:
        この実装は元のcreate_sdk_mcp_server()をベースにしていますが、
        以下の点を修正しています：
        - ツール登録の方法
        - call_toolハンドラーの戻り値形式
        - list_toolsハンドラーの実装
    """
    # MCPサーバーインスタンスを作成
    logger.debug("Creating MCP Server instance: name=%s, version=%s", name, version)
    server = Server(name, version=version)

    # ツールを登録
    if tools:
        logger.debug("Registering %d tools with MCP server", len(tools))
        # ツールマップを作成
        tool_map: dict[str, SdkMcpTool[Any]] = {
            tool_def.name: tool_def for tool_def in tools
        }

        # list_toolsハンドラーを登録
        @server.list_tools()  # type: ignore[misc]
        async def handle_list_tools() -> list[Tool]:
            """利用可能なツールのリストを返す"""
            tool_list = []

            for tool_def in tools:
                # input_schemaをJSON Schema形式に変換
                if isinstance(tool_def.input_schema, dict):
                    # 既にJSON Schemaかチェック
                    if (
                        "type" in tool_def.input_schema
                        and "properties" in tool_def.input_schema
                    ):
                        schema = tool_def.input_schema
                    else:
                        # シンプルなdict（型マッピング）をJSON Schemaに変換
                        properties = {}
                        for param_name, param_type in tool_def.input_schema.items():
                            if param_type is str:
                                properties[param_name] = {"type": "string"}
                            elif param_type is int:
                                properties[param_name] = {"type": "integer"}
                            elif param_type is float:
                                properties[param_name] = {"type": "number"}
                            elif param_type is bool:
                                properties[param_name] = {"type": "boolean"}
                            else:
                                # デフォルト
                                properties[param_name] = {"type": "string"}

                        schema = {
                            "type": "object",
                            "properties": properties,
                            "required": list(properties.keys()),
                        }
                else:
                    # 型が不明な場合は空のスキーマ
                    schema = {"type": "object", "properties": {}}

                tool_list.append(
                    Tool(
                        name=tool_def.name,
                        description=tool_def.description,
                        inputSchema=schema,
                    )
                )

            return tool_list

        # call_toolハンドラーを登録
        @server.call_tool()  # type: ignore[misc]
        async def handle_call_tool(
            name: str, arguments: dict[str, Any]
        ) -> list[TextContent]:
            """ツールを実行する

            Args:
                name: ツール名
                arguments: 引数

            Returns:
                TextContentのリスト

            Raises:
                ValueError: ツールが見つからない場合
            """
            if name not in tool_map:
                raise ValueError(f"Tool '{name}' not found")

            tool_def = tool_map[name]

            # ツールのハンドラーを呼び出し
            result = await tool_def.handler(arguments)

            # 結果をMCP形式に変換
            content: list[TextContent] = []

            if isinstance(result, dict) and "content" in result:
                for item in result["content"]:
                    if isinstance(item, dict) and item.get("type") == "text":
                        content.append(
                            TextContent(type="text", text=item.get("text", ""))
                        )
            else:
                # 結果が辞書でない場合は文字列に変換
                content.append(TextContent(type="text", text=str(result)))

            return content

    # SDK MCPサーバー設定を返す
    return McpSdkServerConfig(type="sdk", name=name, instance=server)
