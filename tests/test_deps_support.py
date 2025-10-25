"""テスト: deps_support モジュール（Milestone 3）

Article 3 (テストファースト) に従って、実装前にテストを作成。
"""

import dataclasses
from typing import Any

import pytest
from pydantic import BaseModel


class TestIsSerializableDeps:
    """is_serializable_deps()のテスト"""

    def test_primitive_types_are_serializable(self) -> None:
        """プリミティブ型はシリアライズ可能"""
        from pydantic_claude_cli.deps_support import is_serializable_deps

        assert is_serializable_deps(str) is True
        assert is_serializable_deps(int) is True
        assert is_serializable_deps(float) is True
        assert is_serializable_deps(bool) is True
        assert is_serializable_deps(type(None)) is True

    def test_collection_types_are_serializable(self) -> None:
        """コレクション型はシリアライズ可能"""
        from pydantic_claude_cli.deps_support import is_serializable_deps

        assert is_serializable_deps(dict) is True
        assert is_serializable_deps(list) is True
        assert is_serializable_deps(tuple) is True

    def test_pydantic_model_is_serializable(self) -> None:
        """Pydanticモデルはシリアライズ可能"""
        from pydantic_claude_cli.deps_support import is_serializable_deps

        class MyModel(BaseModel):
            value: str

        assert is_serializable_deps(MyModel) is True

    def test_simple_dataclass_is_serializable(self) -> None:
        """シンプルなdataclassはシリアライズ可能"""
        from pydantic_claude_cli.deps_support import is_serializable_deps

        @dataclasses.dataclass
        class MyDeps:
            api_key: str
            count: int

        assert is_serializable_deps(MyDeps) is True

    def test_non_serializable_types(self) -> None:
        """非シリアライズ可能な型"""
        from pydantic_claude_cli.deps_support import is_serializable_deps

        # カスタムクラス（BaseModelでもdataclassでもない）
        class CustomClass:
            pass

        assert is_serializable_deps(CustomClass) is False


class TestSerializeDeps:
    """serialize_deps()のテスト"""

    def test_serialize_dict(self) -> None:
        """dictのシリアライズ"""
        from pydantic_claude_cli.deps_support import serialize_deps

        deps = {"api_key": "test123", "count": 42}
        result = serialize_deps(deps)

        assert isinstance(result, str)
        assert '"api_key"' in result
        assert '"test123"' in result

    def test_serialize_list(self) -> None:
        """listのシリアライズ"""
        from pydantic_claude_cli.deps_support import serialize_deps

        deps = [1, 2, 3, "test"]
        result = serialize_deps(deps)

        assert isinstance(result, str)
        assert "1" in result
        assert "test" in result

    def test_serialize_pydantic_model(self) -> None:
        """Pydanticモデルのシリアライズ"""
        from pydantic_claude_cli.deps_support import serialize_deps

        class MyModel(BaseModel):
            value: str
            count: int

        deps = MyModel(value="test", count=42)
        result = serialize_deps(deps)

        assert isinstance(result, str)
        assert '"value"' in result
        assert '"test"' in result

    def test_serialize_dataclass(self) -> None:
        """dataclassのシリアライズ"""
        from pydantic_claude_cli.deps_support import serialize_deps

        @dataclasses.dataclass
        class MyDeps:
            api_key: str
            count: int

        deps = MyDeps(api_key="test123", count=42)
        result = serialize_deps(deps)

        assert isinstance(result, str)
        assert '"api_key"' in result
        assert '"test123"' in result

    def test_serialize_nested_dict(self) -> None:
        """ネストしたdictのシリアライズ"""
        from pydantic_claude_cli.deps_support import serialize_deps

        deps = {"user": {"name": "Alice", "age": 30}, "active": True}
        result = serialize_deps(deps)

        assert isinstance(result, str)
        assert "Alice" in result


class TestDeserializeDeps:
    """deserialize_deps()のテスト"""

    def test_deserialize_dict(self) -> None:
        """dictのデシリアライズ"""
        from pydantic_claude_cli.deps_support import deserialize_deps, serialize_deps

        original = {"api_key": "test123", "count": 42}
        serialized = serialize_deps(original)
        result = deserialize_deps(serialized)

        assert result == original

    def test_deserialize_list(self) -> None:
        """listのデシリアライズ"""
        from pydantic_claude_cli.deps_support import deserialize_deps, serialize_deps

        original = [1, 2, 3, "test"]
        serialized = serialize_deps(original)
        result = deserialize_deps(serialized)

        assert result == original

    def test_deserialize_pydantic_model(self) -> None:
        """Pydanticモデルのデシリアライズ"""
        from pydantic_claude_cli.deps_support import deserialize_deps, serialize_deps

        class MyModel(BaseModel):
            value: str
            count: int

        original = MyModel(value="test", count=42)
        serialized = serialize_deps(original)
        result = deserialize_deps(serialized, deps_type=MyModel)

        assert isinstance(result, MyModel)
        assert result.value == "test"
        assert result.count == 42

    def test_deserialize_dataclass(self) -> None:
        """dataclassのデシリアライズ"""
        from pydantic_claude_cli.deps_support import deserialize_deps, serialize_deps

        @dataclasses.dataclass
        class MyDeps:
            api_key: str
            count: int

        original = MyDeps(api_key="test123", count=42)
        serialized = serialize_deps(original)
        result = deserialize_deps(serialized, deps_type=MyDeps)

        assert isinstance(result, MyDeps)
        assert result.api_key == "test123"
        assert result.count == 42

    def test_deserialize_without_type(self) -> None:
        """型指定なしでデシリアライズ"""
        from pydantic_claude_cli.deps_support import deserialize_deps

        json_str = '{"api_key": "test123", "count": 42}'
        result = deserialize_deps(json_str)

        assert isinstance(result, dict)
        assert result["api_key"] == "test123"
        assert result["count"] == 42

    def test_roundtrip_preserves_data(self) -> None:
        """シリアライズ→デシリアライズで データが保持される"""
        from pydantic_claude_cli.deps_support import deserialize_deps, serialize_deps

        original = {
            "api_key": "secret123",
            "config": {"timeout": 30, "retries": 3},
            "tags": ["prod", "api"],
        }

        serialized = serialize_deps(original)
        restored = deserialize_deps(serialized)

        assert restored == original


class TestSerializationErrors:
    """シリアライズエラーのテスト"""

    def test_serialize_invalid_data(self) -> None:
        """シリアライズできないデータ"""
        from pydantic_claude_cli.deps_support import serialize_deps

        # 循環参照
        circular: dict[str, Any] = {}
        circular["self"] = circular

        with pytest.raises(ValueError, match="Failed to serialize"):
            serialize_deps(circular)

    def test_deserialize_invalid_json(self) -> None:
        """不正なJSON文字列"""
        from pydantic_claude_cli.deps_support import deserialize_deps

        with pytest.raises(ValueError, match="Failed to deserialize"):
            deserialize_deps("{invalid json}")
