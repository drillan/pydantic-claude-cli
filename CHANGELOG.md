# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### カスタムツール機能（Phase 1）🎉

- **依存性なしツール（`@agent.tool_plain`）の完全サポート**
  - 基本型ツール（int, str, float, bool, list, dict）
  - Pydanticモデルを引数に取るツール
  - 同期・非同期ツール対応
  - 複数ツールの自動連携
  - 実際のツール呼び出し動作確認済み

- **新規モジュール**:
  - `tool_support.py`: ツール抽出とRunContext依存性検出
  - `tool_converter.py`: SDK MCP変換機能
  - `mcp_server_fixed.py`: claude-code-sdkバグ回避のための修正版MCPサーバー

- **新規サンプル**:
  - `examples/custom_tools_basic.py`: カスタムツールの基本的な使い方
  - `examples/custom_tools_advanced.py`: Pydanticモデルと非同期ツールの例

- **包括的なドキュメント**:
  - `docs/custom-tools.md`: カスタムツールユーザーガイド
  - `docs/user-guide.md`: 総合ユーザーガイド
  - `docs/internal/`: 内部技術ドキュメント（実装報告、技術詳細）
  - `plans/custom-tools-implementation.md`: 実装計画書

- **テストスイート**:
  - `tests/test_tool_support.py`: tool_supportモジュールのテスト
  - `tests/test_tool_converter.py`: tool_converterモジュールのテスト

#### 技術的改善

- **ClaudeSDKClient統合**: MCPツールが正しく動作するように実装
- **`set_agent_toolsets()`メソッド**: Agentのtoolsetsを設定する機能
- **toolset.tools発見**: ToolDefinitionと実行関数の紐付け問題を解決

### Changed

- **ドキュメント構成の改善**:
  - ユーザー向けドキュメントと内部技術ドキュメントを分離
  - `docs/internal/`に開発者向けドキュメントを配置
  - toctreeを整理（ユーザーガイド / 技術リファレンス）

- **比較表の更新**:
  - `docs/comparison-with-pydantic-ai.md`にカスタムツール機能を反映
  - 判断フローチャートを更新

- **README更新**:
  - カスタムツール使用例を追加
  - サンプルスクリプトリストを追加
  - 機能ステータスを更新（実験的 → 完全動作）

### Fixed

- **claude-code-sdkのバグ回避**:
  - `create_sdk_mcp_server()`の既知のバグ（GitHub Issue #6710）を回避
  - 独自実装`create_fixed_sdk_mcp_server()`を作成
  - `query()`ではなく`ClaudeSDKClient`を使用してMCPツールを動作させる

### Technical Details

- **ツール名プレフィックス**: `mcp__custom__tool_name`形式で参照
- **In-process MCP Server**: サブプロセスではなく同一プロセス内で実行
- **型安全性**: 完全な型アノテーションとmypy検証
- **品質保証**: Article 3（テストファースト）、Article 8（コード品質）、Article 16（型安全性）を完全遵守

### Known Limitations

- **RunContext依存ツール**: `@agent.tool`は未サポート（Phase 3で検討）
- **手動設定が必要**: `model.set_agent_toolsets(agent._function_toolset)`の呼び出しが必須
- **ストリーミング**: 未対応
- **マルチモーダル**: 画像・PDF等未対応

---

## [0.1.0] - 未リリース

### Added

- 初期実装
- `ClaudeCodeCLIModel`: APIキー不要でClaudeモデルにアクセス
- `ClaudeCodeCLIProvider`: CLIプロバイダー実装
- メッセージ変換機能
- エラーハンドリング
- 基本的なドキュメント

### Features

- テキストベース会話の完全サポート
- システムプロンプト対応
- 会話履歴管理
- 使用量トラッキング

---

[Unreleased]: https://github.com/yourusername/pydantic-claude-cli/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/pydantic-claude-cli/releases/tag/v0.1.0
