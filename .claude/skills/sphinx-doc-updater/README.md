# Sphinx ドキュメント更新スキル

このディレクトリには、Claude CodeのAgent Skill `sphinx-doc-updater`が含まれています。

## ファイル構成

```
.claude/skills/sphinx-doc-updater/
├── SKILL.md          # スキルの定義（YAMLフロントマター + 詳細説明）
├── guidelines.md     # ドキュメント作成の詳細ガイドライン
└── README.md         # このファイル
```

## スキルの概要

`sphinx-doc-updater`は、コード変更時にSphinxドキュメントの自動更新を支援するAgent Skillです。

### 主な機能

- コード変更を検知してドキュメント更新の必要性を判断
- 影響を受けるドキュメントファイルを自動特定
- MyST形式とプロジェクト標準に準拠した更新案を作成
- Sphinxビルドのエラーチェック

### 起動条件

以下の場合に自動的に起動します：

1. 公開APIやインターフェースが変更された
2. 新しいクラス、関数、モジュールが追加された
3. アーキテクチャに重要な変更があった
4. ユーザーが明示的にドキュメント更新を依頼
5. コードとドキュメントの不整合を検出

## 使い方

### 自動起動

Claude Codeを使用してコードを変更すると、このスキルが自動的に起動条件を判断し、必要に応じて起動します。

**例**:
```bash
# 新しい機能を実装
claude "ClaudeCodeCLIModelにストリーミング機能を追加してください"

# スキルが自動的に起動し、以下を提案：
# - docs/architecture.md にストリーミングの説明を追加
# - docs/index.md のクイックスタートを更新
# - docs/how-it-works.md にストリーミングの仕組みを追加
```

### 明示的な起動

ドキュメント更新を明示的に依頼することもできます：

```bash
claude "新しく追加したStreamingModelクラスのドキュメントを更新してください"
```

## スキルの動作フロー

1. **変更分析**: コード変更内容を分析
2. **ドキュメント特定**: 影響を受けるドキュメントを特定
3. **更新案作成**: ガイドラインに従って更新案を作成
4. **ユーザー確認**: 更新内容を提示して確認
5. **更新実行**: 承認後にドキュメントを更新
6. **ビルド検証**: Sphinxビルドでエラーチェック

## ドキュメント標準

このスキルは以下の標準に準拠します：

### MyST形式
- MyST (Markedly Structured Text) 構文を使用
- Sphinxディレクティブは ` ```{directive}` 形式

### トーンとスタイル
- 誇張表現を避ける（「革命的」「画期的」など）
- 強調（太字）は本当に必要な場合のみ
- 明確で簡潔な技術文書

### コードブロック
- 適切なシンタックスハイライターを指定
- 実行可能な完全なコード例を提供
- 特殊文字やエラーになる構文を避ける

詳細は `guidelines.md` を参照してください。

## カスタマイズ

### スキルの動作を調整

`SKILL.md`のYAMLフロントマターで調整可能：

```yaml
allowed-tools:
  - Read
  - Edit
  - Write
  - Glob
  - Grep
  - Bash
```

使用可能なツールを制限したい場合は、この配列を編集します。

### ガイドラインの追加

`guidelines.md`に新しいガイドラインを追加することで、スキルの動作をカスタマイズできます。

## トラブルシューティング

### スキルが起動しない

以下を確認：

1. **SKILL.mdの形式**: YAMLフロントマターが正しいか
2. **description**: 起動条件が明確に記述されているか
3. **ファイル名**: `SKILL.md`（大文字）であることを確認

### 更新内容が期待と異なる

1. `guidelines.md`を確認し、必要に応じて編集
2. `SKILL.md`の動作プロセスを調整
3. 明示的に指示を追加（例: "ストリーミング機能のドキュメントをarchitecture.mdに追加"）

### ビルドエラー

Sphinxビルドエラーが発生した場合：

```bash
# エラー詳細を確認
uv run sphinx-build -M html docs docs/_build

# 警告も含めて確認
uv run sphinx-build -M html docs docs/_build 2>&1 | less
```

## 参考資料

- [Claude Code Agent Skills](https://docs.claude.com/en/docs/claude-code/skills)
- [MyST構文ガイド](https://mystmd.org/guide)
- [Sphinxドキュメント](https://www.sphinx-doc.org/)
- プロジェクトのCLAUDE.md（Development Environment > Documentation）

## フィードバック

スキルの改善提案やバグ報告は、プロジェクトのIssueトラッカーに投稿してください。
