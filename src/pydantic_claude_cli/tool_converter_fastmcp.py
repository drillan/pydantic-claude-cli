"""FastMCPベースのツール変換（代替実装）

create_sdk_mcp_server()の既知のバグを回避するため、
FastMCPを使った代替実装を提供します。

Note:
    この実装はstdio MCPサーバーとして外部プロセスで実行されます。
    SDK MCP Server（In-process）とは異なり、サブプロセスのオーバーヘッドがあります。
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Callable

from claude_code_sdk.types import McpStdioServerConfig
from pydantic_ai.tools import ToolDefinition


def create_fastmcp_server_file(
    tools_with_funcs: list[tuple[ToolDefinition, Callable[..., Any]]],
    server_name: str = "pydantic-tools",
) -> Path:
    """FastMCPサーバーのPythonファイルを生成する

    Args:
        tools_with_funcs: (ToolDefinition, 実行関数)のペアリスト
        server_name: MCPサーバー名

    Returns:
        生成されたPythonファイルのパス
    """
    # 一時ファイルを作成
    temp_dir = Path(tempfile.mkdtemp(prefix="pydantic_mcp_"))
    server_file = temp_dir / f"{server_name}_server.py"

    # ツール関数のソースコードを抽出して、FastMCPサーバーファイルを生成
    # NOTE: この実装は複雑で、関数のクロージャや依存関係を正しく処理する必要がある
    # とりあえず、スケルトンのみ実装

    server_code = f'''"""Auto-generated MCP server for pydantic-claude-cli"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("{server_name}")

# TODO: ツール関数を動的に追加
# 課題: Python関数をソースコードとして抽出する必要がある

if __name__ == "__main__":
    mcp.run(transport="stdio")
'''

    server_file.write_text(server_code)
    return server_file


def create_stdio_mcp_config(
    tools_with_funcs: list[tuple[ToolDefinition, Callable[..., Any]]],
) -> McpStdioServerConfig:
    """stdio MCPサーバー設定を作成する（代替実装）

    Args:
        tools_with_funcs: (ToolDefinition, 実行関数)のペアリスト

    Returns:
        McpStdioServerConfig

    Note:
        この実装では、一時ファイルにFastMCPサーバーを生成し、
        stdio経由で実行します。SDK MCP Serverの代替として使用できます。
    """
    # サーバーファイルを生成
    server_file = create_fastmcp_server_file(tools_with_funcs)

    # stdio MCPサーバー設定を返す
    return McpStdioServerConfig(command="python", args=[str(server_file)])


# NOTE: この実装には大きな課題があります：
#
# 1. 関数のソースコード抽出:
#    - inspect.getsource()で取得できるが、クロージャは含まれない
#    - グローバル変数やインポートが失われる
#
# 2. 依存関係の転送:
#    - 関数が使用するモジュールを特定して転送する必要がある
#    - 複雑な依存関係を扱うのは困難
#
# 3. サブプロセスのオーバーヘッド:
#    - stdio MCPサーバーは外部プロセスとして実行される
#    - In-process MCP Serverよりもパフォーマンスが低下
#
# より良いアプローチ: FastMCPを直接使った実装
