"""カスタムツール機能のベンチマーク

このスクリプトは、カスタムツール機能のパフォーマンス特性を測定します。

実行方法:
    uv run python benchmarks/benchmark_custom_tools.py
"""

import asyncio
import sys
import time
from typing import Any

from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel


def benchmark_tool_extraction() -> dict[str, Any]:
    """ツール抽出のオーバーヘッドを測定"""
    from pydantic_ai.tools import ToolDefinition
    from pydantic_claude_cli.tool_support import find_tool_function

    model = ClaudeCodeCLIModel("claude-haiku-4-5")
    agent = Agent(model)
    model.set_agent_toolsets(agent._function_toolset)

    # 5個のツールを定義
    @agent.tool_plain
    def bench_tool_1(x: int) -> int:
        return x + 1

    @agent.tool_plain
    def bench_tool_2(x: int) -> int:
        return x + 2

    @agent.tool_plain
    def bench_tool_3(x: int) -> int:
        return x + 3

    @agent.tool_plain
    def bench_tool_4(x: int) -> int:
        return x + 4

    @agent.tool_plain
    def bench_tool_5(x: int) -> int:
        return x + 5

    # ツール定義リスト
    tool_defs = [
        ToolDefinition(
            name=f"bench_tool_{i}", description="test", parameters_json_schema={}
        )
        for i in range(1, 6)
    ]

    # 測定（10回実行して平均を取る）
    timings = []
    for _ in range(10):
        start = time.perf_counter()
        results = [
            find_tool_function(td, [agent._function_toolset]) for td in tool_defs
        ]
        elapsed = time.perf_counter() - start
        timings.append(elapsed)

    avg_time = sum(timings) / len(timings)
    min_time = min(timings)
    max_time = max(timings)

    return {
        "test": "tool_extraction",
        "num_tools": 5,
        "iterations": 10,
        "avg_ms": avg_time * 1000,
        "min_ms": min_time * 1000,
        "max_ms": max_time * 1000,
        "success": len([r for r in results if r is not None]) == 5,
    }


def benchmark_mcp_server_creation() -> dict[str, Any]:
    """MCPサーバー作成のオーバーヘッドを測定"""
    from pydantic_ai.tools import ToolDefinition
    from pydantic_claude_cli.tool_converter import create_mcp_from_tools

    # 5個のツール定義
    tools_with_funcs = []
    for i in range(5):

        def func(x: int, _i: int = i) -> int:
            return x + _i

        tool_def = ToolDefinition(
            name=f"mcp_tool_{i}",
            description=f"Tool {i}",
            parameters_json_schema={
                "type": "object",
                "properties": {"x": {"type": "integer"}},
            },
        )
        tools_with_funcs.append((tool_def, func))

    # 測定（10回実行）
    timings = []
    for _ in range(10):
        start = time.perf_counter()
        server = create_mcp_from_tools(tools_with_funcs)
        elapsed = time.perf_counter() - start
        timings.append(elapsed)

    avg_time = sum(timings) / len(timings)
    min_time = min(timings)
    max_time = max(timings)

    return {
        "test": "mcp_server_creation",
        "num_tools": 5,
        "iterations": 10,
        "avg_ms": avg_time * 1000,
        "min_ms": min_time * 1000,
        "max_ms": max_time * 1000,
        "success": server["type"] == "sdk",
    }


def benchmark_memory_usage() -> dict[str, Any]:
    """メモリ使用量を測定"""
    model = ClaudeCodeCLIModel("claude-haiku-4-5")
    agent = Agent(model)
    model.set_agent_toolsets(agent._function_toolset)

    # 3個のツールを定義
    @agent.tool_plain
    def mem_tool_1(x: int) -> int:
        return x + 1

    @agent.tool_plain
    def mem_tool_2(x: int) -> int:
        return x + 2

    @agent.tool_plain
    def mem_tool_3(x: int) -> int:
        return x + 3

    model_size = sys.getsizeof(model)
    agent_size = sys.getsizeof(agent)

    return {
        "test": "memory_usage",
        "model_size_bytes": model_size,
        "agent_size_bytes": agent_size,
        "model_size_mb": model_size / (1024 * 1024),
        "agent_size_mb": agent_size / (1024 * 1024),
    }


async def benchmark_end_to_end() -> dict[str, Any]:
    """E2Eパフォーマンスを測定"""
    model = ClaudeCodeCLIModel("claude-haiku-4-5")
    agent = Agent(model)
    model.set_agent_toolsets(agent._function_toolset)

    @agent.tool_plain
    def add(x: int, y: int) -> int:
        return x + y

    # シンプルなツール呼び出しの時間を測定
    start = time.perf_counter()
    result = await agent.run("Use add tool to calculate 5 + 3")
    elapsed = time.perf_counter() - start

    return {
        "test": "end_to_end_with_tool",
        "elapsed_seconds": elapsed,
        "success": result.output is not None,
    }


def main() -> None:
    """ベンチマークを実行"""
    print("=" * 70)
    print("pydantic-claude-cli パフォーマンスベンチマーク")
    print("=" * 70)
    print()

    # ツール抽出
    print("【1】ツール抽出のオーバーヘッド")
    result1 = benchmark_tool_extraction()
    print(f"  平均: {result1['avg_ms']:.3f}ms")
    print(f"  最小: {result1['min_ms']:.3f}ms")
    print(f"  最大: {result1['max_ms']:.3f}ms")
    print(f"  成功: {result1['success']}")
    print()

    # MCPサーバー作成
    print("【2】MCPサーバー作成のオーバーヘッド")
    result2 = benchmark_mcp_server_creation()
    print(f"  平均: {result2['avg_ms']:.3f}ms")
    print(f"  最小: {result2['min_ms']:.3f}ms")
    print(f"  最大: {result2['max_ms']:.3f}ms")
    print(f"  成功: {result2['success']}")
    print()

    # メモリ使用量
    print("【3】メモリ使用量")
    result3 = benchmark_memory_usage()
    print(
        f"  Model: {result3['model_size_bytes']:,} bytes ({result3['model_size_mb']:.3f} MB)"
    )
    print(
        f"  Agent: {result3['agent_size_bytes']:,} bytes ({result3['agent_size_mb']:.3f} MB)"
    )
    print()

    # E2E
    print("【4】E2Eパフォーマンス（カスタムツール使用）")
    print("  実行中...")
    result4 = asyncio.run(benchmark_end_to_end())
    print(f"  実行時間: {result4['elapsed_seconds']:.2f}秒")
    print(f"  成功: {result4['success']}")
    print()

    # サマリー
    print("=" * 70)
    print("サマリー")
    print("=" * 70)
    print()
    print(f"ツール抽出:        {result1['avg_ms']:.3f}ms（5ツール）")
    print(f"MCPサーバー作成:   {result2['avg_ms']:.3f}ms（5ツール）")
    print(
        f"メモリ使用量:      Model {result3['model_size_mb']:.3f}MB, Agent {result3['agent_size_mb']:.3f}MB"
    )
    print(f"E2E実行時間:       {result4['elapsed_seconds']:.2f}秒")
    print()
    print("=" * 70)
    print("✅ ベンチマーク完了")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n中断されました")
    except Exception as e:
        print(f"\n\n❌ エラー: {e}")
        import traceback

        traceback.print_exc()
