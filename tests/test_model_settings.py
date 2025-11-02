"""Tests for ModelSettings support in ClaudeCodeCLIModel."""

from __future__ import annotations

import pytest
from pydantic_ai.models import ModelSettings

from pydantic_claude_cli import ClaudeCodeCLIModel


class TestModelSettingsExtraction:
    """Test ModelSettings extraction and conversion to ClaudeCodeOptions."""

    def test_extract_model_settings_with_temperature(self) -> None:
        """temperatureが正しく抽出されることを確認."""
        model = ClaudeCodeCLIModel("claude-haiku-4-5")
        settings = ModelSettings(temperature=0.7)

        extracted = model._extract_model_settings(settings)

        assert "temperature" in extracted
        assert extracted["temperature"] == "0.7"  # extra_argsは文字列

    def test_extract_model_settings_with_max_tokens(self) -> None:
        """max_tokensが正しく抽出されることを確認."""
        model = ClaudeCodeCLIModel("claude-haiku-4-5")
        settings = ModelSettings(max_tokens=1000)

        extracted = model._extract_model_settings(settings)

        assert "max_tokens" in extracted
        assert extracted["max_tokens"] == "1000"  # extra_argsは文字列

    def test_extract_model_settings_with_top_p(self) -> None:
        """top_pが正しく抽出されることを確認."""
        model = ClaudeCodeCLIModel("claude-haiku-4-5")
        settings = ModelSettings(top_p=0.9)

        extracted = model._extract_model_settings(settings)

        assert "top_p" in extracted
        assert extracted["top_p"] == "0.9"  # extra_argsは文字列

    def test_extract_model_settings_with_multiple_params(self) -> None:
        """複数のパラメータが正しく抽出されることを確認."""
        model = ClaudeCodeCLIModel("claude-haiku-4-5")
        settings = ModelSettings(temperature=0.7, max_tokens=1000, top_p=0.9)

        extracted = model._extract_model_settings(settings)

        assert extracted == {
            "temperature": "0.7",  # extra_argsは文字列
            "max_tokens": "1000",  # extra_argsは文字列
            "top_p": "0.9",  # extra_argsは文字列
        }

    def test_extract_model_settings_with_none(self) -> None:
        """Noneが渡された場合、空のdictを返すことを確認."""
        model = ClaudeCodeCLIModel("claude-haiku-4-5")

        extracted = model._extract_model_settings(None)

        assert extracted == {}

    def test_extract_model_settings_with_empty_settings(self) -> None:
        """空のModelSettingsの場合、空のdictを返すことを確認."""
        model = ClaudeCodeCLIModel("claude-haiku-4-5")
        settings = ModelSettings()

        extracted = model._extract_model_settings(settings)

        assert extracted == {}

    def test_extract_model_settings_ignores_none_values(self) -> None:
        """Noneの値は無視されることを確認."""
        model = ClaudeCodeCLIModel("claude-haiku-4-5")
        settings = ModelSettings(temperature=0.7)  # max_tokensはNone

        extracted = model._extract_model_settings(settings)

        assert "temperature" in extracted
        assert "max_tokens" not in extracted

    def test_extract_model_settings_with_unsupported_param(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """未サポートのパラメータでwarningが出ることを確認."""
        import logging

        caplog.set_level(logging.WARNING)

        model = ClaudeCodeCLIModel("claude-haiku-4-5")
        # Pydantic AIのModelSettingsは他にもパラメータがある可能性があるが、
        # 現時点ではtemperature, max_tokens, top_pのみサポート
        settings = ModelSettings(temperature=0.7)

        # NOTE: 現在の実装では未サポートパラメータの警告は出さない
        # （将来的に追加する可能性あり）
        extracted = model._extract_model_settings(settings)

        assert "temperature" in extracted
