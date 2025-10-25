"""依存性のContextVar管理

このモジュールは、Pydantic AIの既存ContextVarパターン（_messages_ctx_var）と
同じアプローチで依存性を転送します。

Milestone 3の一部として実装されました。

Example:
    ```python
    from pydantic_claude_cli.deps_context import set_current_deps, get_current_deps, reset_deps

    # 依存性を設定（型情報付き）
    token = set_current_deps({"api_key": "abc123"}, deps_type=dict)
    try:
        # 依存性を取得
        deps, deps_type = get_current_deps()
        print(deps)  # {'api_key': 'abc123'}
        print(deps_type)  # <class 'dict'>
    finally:
        # クリーンアップ
        reset_deps(token)
    ```
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

__all__ = (
    "set_current_deps",
    "get_current_deps",
    "get_current_deps_with_type",
    "reset_deps",
    "DepsData",
)


@dataclass
class DepsData:
    """依存性とその型情報を保持するデータクラス"""

    deps: Any
    deps_type: type | None = None


# グローバルContextVar
# Pydantic AIの_messages_ctx_varと同じパターン
_deps_ctx_var: ContextVar[DepsData] = ContextVar("pydantic_claude_cli_deps")


def set_current_deps(deps: Any, deps_type: type | None = None) -> Any:
    """現在の依存性をContextVarに設定する

    Args:
        deps: 設定する依存性
        deps_type: 依存性の型（Pydanticモデルやdataclassの場合）

    Returns:
        リセット用のトークン

    Example:
        >>> from pydantic import BaseModel
        >>> class Config(BaseModel):
        ...     api_key: str
        >>> config = Config(api_key="abc123")
        >>> token = set_current_deps(config, deps_type=Config)
        >>> # ... 処理 ...
        >>> reset_deps(token)

    Note:
        必ずfinally節でreset_deps()を呼び出してクリーンアップしてください。
        deps_typeを指定すると、deserialize時に正しく型変換されます。
    """
    return _deps_ctx_var.set(DepsData(deps=deps, deps_type=deps_type))


def get_current_deps() -> Any | None:
    """現在の依存性をContextVarから取得する（依存性のみ）

    Returns:
        依存性、または設定されていない場合はNone

    Example:
        >>> deps = get_current_deps()
        >>> if deps:
        ...     api_key = deps.get("api_key")

    Note:
        set_current_deps()が呼ばれていない場合、Noneを返します。
        型情報も必要な場合は、get_current_deps_with_type()を使用してください。
    """
    try:
        data = _deps_ctx_var.get()
        return data.deps
    except LookupError:
        return None


def get_current_deps_with_type() -> tuple[Any, type | None] | None:
    """現在の依存性と型情報をContextVarから取得する

    Returns:
        (依存性, deps_type)のタプル、または設定されていない場合はNone

    Example:
        >>> result = get_current_deps_with_type()
        >>> if result:
        ...     deps, deps_type = result
        ...     api_key = deps.get("api_key")

    Note:
        set_current_deps()が呼ばれていない場合、Noneを返します。
    """
    try:
        data = _deps_ctx_var.get()
        return (data.deps, data.deps_type)
    except LookupError:
        return None


def reset_deps(token: Any) -> None:
    """依存性をリセットする

    Args:
        token: set_current_deps()で取得したトークン

    Example:
        >>> token = set_current_deps({"api_key": "abc123"})
        >>> try:
        ...     # 処理
        ...     pass
        ... finally:
        ...     reset_deps(token)

    Note:
        必ずfinally節で呼び出してください。
        ネストした場合は、最後に設定したものから順にリセットしてください。
    """
    _deps_ctx_var.reset(token)
