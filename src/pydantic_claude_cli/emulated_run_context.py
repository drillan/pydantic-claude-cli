"""RunContextのエミュレーション（制限版）

このモジュールは、RunContextの最小限の機能を提供します。
完全なRunContextはサポートされていません。

Milestone 3の一部として実装されました。

Example:
    ```python
    from pydantic_claude_cli.emulated_run_context import EmulatedRunContext

    # 依存性のみを持つRunContextをエミュレート
    ctx = EmulatedRunContext(deps={"api_key": "abc123"})

    # depsプロパティにアクセス可能
    print(ctx.deps["api_key"])  # 'abc123'

    # 他のプロパティはエラー
    try:
        ctx.retry()
    except AttributeError as e:
        print(e)  # "EmulatedRunContext has no attribute 'retry'"
    ```
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

__all__ = ("EmulatedRunContext",)

DepsT = TypeVar("DepsT")


class EmulatedRunContext(Generic[DepsT]):
    """RunContextの制限版エミュレーション

    このクラスは、ツール実行時にRunContextをエミュレートします。
    ただし、以下の制限があります：

    - `deps`のみ使用可能
    - `retry`, `run_step`, `usage`等は未サポート

    Warning:
        これは完全なRunContextではありません。
        `deps`以外のプロパティにアクセスするとAttributeErrorが発生します。

    Example:
        >>> from pydantic_claude_cli.emulated_run_context import EmulatedRunContext
        >>> ctx = EmulatedRunContext(deps={"api_key": "abc123"})
        >>> ctx.deps["api_key"]
        'abc123'
        >>> ctx.retry()  # doctest: +SKIP
        Traceback (most recent call last):
            ...
        AttributeError: 'EmulatedRunContext' has no attribute 'retry'. ...

    Note:
        完全なRunContextサポートが必要な場合は、Pydantic AI標準
        （AnthropicModel）を使用してください。
    """

    def __init__(self, deps: DepsT):
        """EmulatedRunContextを初期化

        Args:
            deps: 依存性

        Example:
            >>> ctx = EmulatedRunContext(deps={"api_key": "test123"})
            >>> ctx.deps
            {'api_key': 'test123'}
        """
        self._deps = deps

    @property
    def deps(self) -> DepsT:
        """依存性を取得

        Returns:
            依存性

        Example:
            >>> ctx = EmulatedRunContext(deps={"key": "value"})
            >>> ctx.deps
            {'key': 'value'}
        """
        return self._deps

    def __getattr__(self, name: str) -> Any:
        """未サポートのプロパティへのアクセスをエラーにする

        Args:
            name: プロパティ名

        Raises:
            AttributeError: 未サポートのプロパティ

        Example:
            >>> ctx = EmulatedRunContext(deps={})
            >>> ctx.retry()  # doctest: +SKIP
            Traceback (most recent call last):
                ...
            AttributeError: 'EmulatedRunContext' has no attribute 'retry'. ...
        """
        raise AttributeError(
            f"'{self.__class__.__name__}' has no attribute '{name}'. "
            f"Only 'deps' is supported in emulated RunContext. "
            f"For full RunContext support, use Pydantic AI standard (AnthropicModel)."
        )
