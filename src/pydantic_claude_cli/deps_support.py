"""依存性のシリアライズとバリデーション

このモジュールは、依存性がシリアライズ可能かチェックし、
JSON文字列への変換/復元を行います。

Milestone 3の一部として実装されました。

Example:
    ```python
    from pydantic_claude_cli.deps_support import (
        is_serializable_deps,
        serialize_deps,
        deserialize_deps,
    )

    # シリアライズ可能かチェック
    if is_serializable_deps(dict):
        # シリアライズ
        deps_json = serialize_deps({"api_key": "abc123"})

        # デシリアライズ
        deps = deserialize_deps(deps_json)
    ```
"""

from __future__ import annotations

import dataclasses
import json
import logging
from typing import Any

from pydantic import BaseModel

__all__ = ("is_serializable_deps", "serialize_deps", "deserialize_deps")

logger = logging.getLogger(__name__)

# シリアライズ可能な基本型
_SERIALIZABLE_TYPES = (str, int, float, bool, type(None), dict, list, tuple)


def is_serializable_deps(deps_type: type) -> bool:
    """依存性がシリアライズ可能かチェックする

    Args:
        deps_type: チェックする型

    Returns:
        シリアライズ可能ならTrue

    Example:
        >>> is_serializable_deps(dict)
        True
        >>> is_serializable_deps(str)
        True
        >>> import httpx
        >>> is_serializable_deps(httpx.AsyncClient)
        False

    Note:
        以下の型をシリアライズ可能と判断します:
        - プリミティブ型: str, int, float, bool, None
        - コレクション型: dict, list, tuple
        - Pydanticモデル: BaseModel
        - シンプルなdataclass（すべてのフィールドがシリアライズ可能）
    """
    # 基本型チェック
    if deps_type in _SERIALIZABLE_TYPES:
        return True

    # Pydanticモデルチェック
    try:
        if issubclass(deps_type, BaseModel):
            return True
    except TypeError:
        pass

    # dataclassチェック
    if dataclasses.is_dataclass(deps_type):
        # すべてのフィールドがシリアライズ可能かチェック
        for field in dataclasses.fields(deps_type):  # type: ignore[arg-type]
            # field.typeがtypeでない場合はスキップ（型アノテーションが複雑な場合）
            if not isinstance(field.type, type):
                logger.warning(
                    "Dataclass field '%s' has complex type annotation, skipping check",
                    field.name,
                )
                continue

            if not is_serializable_deps(field.type):
                logger.warning(
                    "Dataclass field '%s' has non-serializable type '%s'",
                    field.name,
                    field.type,
                )
                return False
        return True

    # その他は非シリアライズ可能
    logger.debug("Type '%s' is not serializable", deps_type)
    return False


def serialize_deps(deps: Any) -> str:
    """依存性をJSON文字列にシリアライズする

    Args:
        deps: シリアライズする依存性

    Returns:
        JSON文字列

    Raises:
        ValueError: シリアライズに失敗した場合

    Example:
        >>> serialize_deps({"api_key": "abc123"})
        '{"api_key": "abc123"}'

    Note:
        以下の型をサポートします:
        - Pydanticモデル: model_dump_json()を使用
        - dataclass: dataclasses.asdict()を使用
        - その他（dict, list等）: json.dumps()を使用
    """
    try:
        # Pydanticモデルの場合
        if isinstance(deps, BaseModel):
            return deps.model_dump_json()

        # dataclassの場合
        if dataclasses.is_dataclass(deps):
            return json.dumps(dataclasses.asdict(deps))  # type: ignore[arg-type]

        # その他（dict, list等）
        return json.dumps(deps)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Failed to serialize dependencies: {e}") from e


def deserialize_deps(deps_json: str, deps_type: type | None = None) -> Any:
    """JSON文字列から依存性を復元する

    Args:
        deps_json: JSON文字列
        deps_type: 復元する型（Pydanticモデルやdataclassの場合）

    Returns:
        復元された依存性

    Raises:
        ValueError: デシリアライズに失敗した場合

    Example:
        >>> deserialize_deps('{"api_key": "abc123"}')
        {'api_key': 'abc123'}

        >>> from pydantic import BaseModel
        >>> class MyModel(BaseModel):
        ...     api_key: str
        >>> deserialize_deps('{"api_key": "abc123"}', deps_type=MyModel)
        MyModel(api_key='abc123')

    Note:
        deps_typeが指定されていない場合、単純にJSON解析を行います。
        Pydanticモデルやdataclassの場合は、deps_typeを指定してください。
    """
    try:
        # 型指定がない場合は単純にJSON解析
        if deps_type is None:
            return json.loads(deps_json)

        # Pydanticモデルの場合
        if isinstance(deps_type, type) and issubclass(deps_type, BaseModel):
            return deps_type.model_validate_json(deps_json)

        # dataclassの場合
        if dataclasses.is_dataclass(deps_type):
            data = json.loads(deps_json)
            return deps_type(**data)

        # その他
        return json.loads(deps_json)
    except (TypeError, ValueError, json.JSONDecodeError) as e:
        raise ValueError(f"Failed to deserialize dependencies: {e}") from e
