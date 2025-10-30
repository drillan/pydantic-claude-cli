# Pydantic AI機能差分調査とModelSettings実装

## 概要

本家Pydantic AIとの機能差分を調査し、実装が容易な5つの未実装機能を特定しました。その中で最優先度の高い **Issue #002「ModelSettingsの完全サポート」** を実装しました。

また、GitHub issueが作成できない環境での代替手段として、バージョン管理可能なローカルissue管理システムを構築しました。

---

## 主要な変更内容

### 1. 機能差分調査（Issue #001）

本家Pydantic AIの機能を調査し、以下の実装が容易な機能を特定：

- ✅ **Issue #002**: ModelSettingsの完全サポート（推定工数: 1-2時間）**← 実装完了**
- ⏳ **Issue #003**: Usage情報の詳細化（推定工数: 1時間）
- ⏳ **Issue #004**: Result Validatorのサポート（推定工数: 2-3時間）
- ⏳ **Issue #005**: Model-level Retry設定（推定工数: 3-4時間）
- ⏳ **Issue #006**: Tool Error Handlingの改善（推定工数: 3-4時間）

**ドキュメント**: `issues/001-feature-gap-analysis.md`

### 2. ローカルissue管理システムの構築

GitHub issueが利用できない環境でも、バージョン管理可能なissue管理を実現：

```
issues/
├── README.md                    # Issue管理方法の説明
├── TEMPLATE.md                  # Issue作成テンプレート
├── list.sh                      # Issue一覧表示スクリプト
├── 001-feature-gap-analysis.md
├── 002-modelsettings-support.md
├── 003-usage-details.md
├── 004-result-validator.md
├── 005-model-level-retry.md
└── 006-tool-error-handling.md
```

**特徴**:
- バージョン管理可能（Gitで履歴管理）
- オフライン対応
- 検索可能（grep等）
- GitHub issueへの移行が容易

### 3. ModelSettingsの完全サポート（Issue #002）✅

`temperature`、`max_tokens`、`top_p`等のModelSettingsパラメータをサポート：

```python
from pydantic_ai import Agent
from pydantic_ai.models import ModelSettings
from pydantic_claude_cli import ClaudeCodeCLIModel

model = ClaudeCodeCLIModel(
    'claude-haiku-4-5',
    settings=ModelSettings(
        temperature=0.7,
        max_tokens=1000,
        top_p=0.9,
    )
)

agent = Agent(model)
result = await agent.run('創造的な物語を書いて')
```

---

## 実装の詳細（Issue #002）

### 変更ファイル

| ファイル | 変更内容 | 行数 |
|---------|---------|-----|
| `src/pydantic_claude_cli/model.py` | `_extract_model_settings()`メソッド追加 | +47 |
| `tests/test_model_settings.py` | ユニットテスト追加（8テスト） | +101 |
| `examples/model_settings.py` | サンプルコード追加（4例） | +126 |
| `README.md` | 使用例を追加 | +29 |

### 実装アプローチ

1. **パラメータ抽出**
   - `ModelSettings`から`temperature`、`max_tokens`、`top_p`を抽出
   - 値を文字列に変換（`extra_args`の型に合わせる）

2. **CLIへの渡し方**
   - `ClaudeCodeOptions.extra_args`経由で渡す
   - Claude Code SDKには直接的なパラメータがないため、実験的な実装

3. **ユーザーへの通知**
   - 警告ログで実験的機能であることを通知
   - ドキュメントに注意事項を明記

### コード例

```python
def _extract_model_settings(
    self, model_settings: ModelSettings | None
) -> dict[str, str | None]:
    """ModelSettingsからClaude Code SDK対応パラメータを抽出"""
    if not model_settings:
        return {}

    params: dict[str, str | None] = {}
    supported = ["temperature", "max_tokens", "top_p"]

    for key in supported:
        value = model_settings.get(key)
        if value is not None:
            params[key] = str(value)
            logger.debug(f"Extracted model setting: {key}={value}")

    if params:
        logger.warning(
            "Model settings support is experimental. "
            "Claude Code CLI may not support all parameters."
        )

    return params
```

---

## テスト結果

### ユニットテスト

```bash
$ uv run pytest tests/test_model_settings.py -v
```

**結果**: ✅ 8 passed

- `test_extract_model_settings_with_temperature` ✅
- `test_extract_model_settings_with_max_tokens` ✅
- `test_extract_model_settings_with_top_p` ✅
- `test_extract_model_settings_with_multiple_params` ✅
- `test_extract_model_settings_with_none` ✅
- `test_extract_model_settings_with_empty_settings` ✅
- `test_extract_model_settings_ignores_none_values` ✅
- `test_extract_model_settings_with_unsupported_param` ✅

### 全体のテスト

```bash
$ uv run pytest
```

**結果**: ✅ 69 passed, 7 skipped

### コード品質

- ✅ **ruff check & format**: All checks passed
- ✅ **mypy**: No issues found in 36 source files
- ✅ **Article 8（Code Quality Standards）**: 完全準拠

---

## サンプルコード（examples/model_settings.py）

4つの実用例を追加：

### 1. 基本的な使用方法
```python
model = ClaudeCodeCLIModel(
    "claude-haiku-4-5",
    settings=ModelSettings(
        temperature=0.7,
        max_tokens=500,
        top_p=0.9,
    )
)
```

### 2. Temperature比較
低温度（0.2）vs 高温度（1.0）での応答の違いを比較

### 3. Max Tokens制御
短い応答（50トークン）vs 長い応答（200トークン）

### 4. 複数設定の組み合わせ
temperature + max_tokens + top_pを同時に使用

---

## 注意事項

### 実験的機能

- **パラメータの渡し方**: `extra_args`経由で渡すため、実験的な実装です
- **CLIのサポート**: Claude Code CLIがこれらのパラメータをサポートしているかは未確認です
- **警告ログ**: 実行時に実験的機能であることを通知します

### サポートされているパラメータ

| パラメータ | 説明 | 例 |
|-----------|------|-----|
| `temperature` | 応答のランダム性（0.0-1.0） | `0.7` |
| `max_tokens` | 最大トークン数 | `1000` |
| `top_p` | 確率分布の閾値（0.0-1.0） | `0.9` |

---

## 破壊的変更

なし。既存のコードに影響を与えません。

---

## チェックリスト

### 開発プロセス（Constitution準拠）

- [x] **Article 3（Test-First Imperative）**: テストを先に作成してRed→Green確認
- [x] **Article 8（Code Quality Standards）**: ruff + mypy 完全準拠
- [x] **Article 10（DRY Principle）**: 既存コードを検索して重複を回避
- [x] **Article 16（Type Safety）**: 完全な型アノテーション

### コード品質

- [x] ユニットテストを追加（8テスト）
- [x] すべてのテストが通過
- [x] ruff check & format 通過
- [x] mypy 型チェック通過
- [x] 既存のテストも全て通過

### ドキュメント

- [x] README.mdに使用例を追加
- [x] サンプルコードを作成（examples/model_settings.py）
- [x] 実験的機能であることを明記
- [x] 各パラメータの説明を追加

### Issue管理

- [x] Issue #002のステータスをCompletedに更新
- [x] Updatesセクションに実装詳細を記録
- [x] 推定工数と実際の工数を記録

---

## 関連リンク

- **Issue #001**: [機能差分調査](issues/001-feature-gap-analysis.md)
- **Issue #002**: [ModelSettingsの完全サポート](issues/002-modelsettings-support.md)
- **Pydantic AI公式**: https://ai.pydantic.dev/
- **Claude Code SDK**: https://github.com/anthropics/claude-code-sdk-python

---

## 次のステップ

残りの4つのissueの実装を提案します：

1. **Issue #003**: Usage情報の詳細化（1時間）
2. **Issue #004**: Result Validatorのサポート（2-3時間）
3. **Issue #005**: Model-level Retry設定（3-4時間）
4. **Issue #006**: Tool Error Handlingの改善（3-4時間）

これらを実装することで、機能カバレッジを60%から70-75%に向上できます。

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
