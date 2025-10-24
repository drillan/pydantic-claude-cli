"""カスタムツールサポートのメインロジック

このモジュールは、Pydantic AIのカスタムツールをClaude Code CLIで
使用可能にするための中核機能を提供します。

主な機能:
- ツールと実行関数の抽出
- RunContext依存性の検出
- FunctionToolsetからの関数検索
"""

from __future__ import annotations

import inspect
from typing import Any, Callable

from pydantic_ai.models import ModelRequestParameters
from pydantic_ai.toolsets import AbstractToolset
from pydantic_ai.tools import RunContext, ToolDefinition


def requires_run_context(func: Callable[..., Any]) -> bool:
    """関数がRunContextパラメータを必要とするかチェックする

    Args:
        func: チェックする関数

    Returns:
        RunContextパラメータを持つ場合True

    Example:
        >>> from pydantic_ai.tools import RunContext
        >>>
        >>> async def tool_with_context(ctx: RunContext[str], x: int) -> str:
        ...     return f"{ctx.deps}: {x}"
        >>>
        >>> requires_run_context(tool_with_context)
        True
        >>>
        >>> def tool_without_context(x: int, y: int) -> int:
        ...     return x + y
        >>>
        >>> requires_run_context(tool_without_context)
        False
    """
    try:
        sig = inspect.signature(func)
    except (ValueError, TypeError):
        # シグネチャを取得できない場合は、依存性なしと判断
        return False

    for param_name, param in sig.parameters.items():
        # 型アノテーションがない場合はスキップ
        if param.annotation == inspect.Parameter.empty:
            continue

        annotation = param.annotation

        # 直接的なRunContextチェック
        try:
            if isinstance(annotation, type) and issubclass(annotation, RunContext):
                return True
        except TypeError:
            # isinstance/issubclassでエラーが出る場合は、
            # Genericタイプの可能性がある
            pass

        # Generic RunContext[T]のチェック
        origin = getattr(annotation, "__origin__", None)
        if origin is RunContext:
            return True

        # typing.Annotatedなどの複雑なケース
        if hasattr(annotation, "__args__"):
            for arg in annotation.__args__:
                try:
                    if isinstance(arg, type) and issubclass(arg, RunContext):
                        return True
                except TypeError:
                    pass

    return False


def find_tool_function(
    tool_def: ToolDefinition, toolsets: list[AbstractToolset] | None
) -> Callable[..., Any] | None:
    """toolsetsから対応する実行関数を見つける

    Args:
        tool_def: ToolDefinition
        toolsets: toolsetsリスト

    Returns:
        見つかった関数、見つからなければNone

    Note:
        この実装はtoolsetの.tools属性を使用しています。
        toolsはdict[str, Tool]で、Toolオブジェクトに実行関数への参照があります。
    """
    if not toolsets:
        return None

    for toolset in toolsets:
        # toolset.tools属性をチェック（_AgentFunctionToolsetが持つ）
        if hasattr(toolset, "tools"):
            tools_dict = getattr(toolset, "tools")
            if isinstance(tools_dict, dict) and tool_def.name in tools_dict:
                tool_obj = tools_dict[tool_def.name]
                # Toolオブジェクトからfunctionを取得
                if hasattr(tool_obj, "function"):
                    return tool_obj.function

    return None


def extract_tools_from_agent(
    model_request_parameters: ModelRequestParameters,
    agent_toolsets: list[AbstractToolset] | None = None,
) -> tuple[list[tuple[ToolDefinition, Callable[..., Any]]], bool]:
    """Agentからツールと実行関数を抽出する

    Args:
        model_request_parameters: モデルリクエストパラメータ
        agent_toolsets: Agentのtoolsetsリスト

    Returns:
        (ツールと関数のペアリスト, RunContext依存ツールがあるか)

    Raises:
        MessageConversionError: ツール抽出に失敗した場合

    Example:
        >>> from pydantic_ai.models import ModelRequestParameters
        >>> params = ModelRequestParameters(function_tools=[...])
        >>> tools, has_context = extract_tools_from_agent(params)
    """
    tools_with_funcs: list[tuple[ToolDefinition, Callable[..., Any]]] = []
    has_context_tools = False

    # function_toolsを処理
    function_tools = model_request_parameters.function_tools or []

    for tool_def in function_tools:
        # toolsetsから対応する関数を探す
        func = find_tool_function(tool_def, agent_toolsets)

        if func is None:
            # 関数が見つからない場合はスキップ
            # NOTE: set_agent_toolsets()が呼び出されていない可能性
            continue

        # RunContext依存性をチェック
        if requires_run_context(func):
            has_context_tools = True

        tools_with_funcs.append((tool_def, func))

    return tools_with_funcs, has_context_tools
