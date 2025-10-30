# [003] Usage情報の詳細化

**Status**: Open
**Priority**: Medium
**Labels**: `enhancement`
**Assignee**: (未割当)
**Related Issues**: #001
**GitHub Issue**: (未作成)
**Created**: 2025-10-30
**Updated**: 2025-10-30

---

## 概要

`result_message.usage`から詳細メトリクス（cache hits, thinking tokens等）を抽出し、`ModelResponse.usage`に含める。

---

## 問題・動機

現在、基本的なtoken countとcostは取得済みだが、Claude Code CLIが提供する詳細メトリクスが活用されていない。これにより、デバッグやコスト最適化が困難。

**現在取得しているもの**:
- `input_tokens`
- `output_tokens`
- `total_cost_usd`

**未取得のもの**:
- Cache hits/misses
- Thinking tokens (extended thinking)
- Tool use tokens
- その他詳細メトリクス

---

## 提案

### 実装方針

1. `message_converter.py:147` の `extract_usage_from_result()` を拡張
2. `result_message.usage` の全フィールドを調査
3. `ModelResponse.usage` に追加情報を含める（Pydantic AIの`Usage`モデルに対応）
4. ログ出力で詳細情報を確認できるようにする

### 技術的詳細

**修正箇所**: `src/pydantic_claude_cli/message_converter.py:147-182`

```python
# 現在のコード
def extract_usage_from_result(result_data: dict[str, Any]) -> Usage:
    """Extract usage information from Claude CLI result."""
    usage_data = result_data.get("usage", {})

    return Usage(
        requests=1,
        request_tokens=usage_data.get("input_tokens", 0),
        response_tokens=usage_data.get("output_tokens", 0),
        total_tokens=usage_data.get("input_tokens", 0)
        + usage_data.get("output_tokens", 0),
        # 追加: 詳細メトリクス
    )

# 提案する変更
def extract_usage_from_result(result_data: dict[str, Any]) -> Usage:
    """Extract detailed usage information from Claude CLI result."""
    usage_data = result_data.get("usage", {})

    # 基本メトリクス
    input_tokens = usage_data.get("input_tokens", 0)
    output_tokens = usage_data.get("output_tokens", 0)

    # 詳細メトリクス（Claude SDKが提供する場合）
    cache_creation_tokens = usage_data.get("cache_creation_input_tokens", 0)
    cache_read_tokens = usage_data.get("cache_read_input_tokens", 0)

    # Pydantic AI の Usage モデルに合わせる
    details = {
        "cache_creation_tokens": cache_creation_tokens,
        "cache_read_tokens": cache_read_tokens,
        # その他のメトリクス
    }

    return Usage(
        requests=1,
        request_tokens=input_tokens,
        response_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        details=details,  # 追加情報
    )
```

**調査が必要**:
- `result_message.usage`に含まれる全フィールド
- Pydantic AIの`Usage`モデルが受け付けるフィールド
- `details`フィールドの使い方

---

## タスク

- [ ] `result_message.usage`の全フィールドを調査
- [ ] Pydantic AIの`Usage`モデルの仕様を確認
- [ ] `extract_usage_from_result()`を拡張
- [ ] 詳細メトリクスをログ出力に追加
- [ ] テストケース追加（`tests/test_message_converter.py`）
  - [ ] 詳細usageが正しく抽出されることを確認
  - [ ] cache metricsが正しく処理されることを確認
- [ ] ドキュメント更新（使用量トラッキングの説明）
- [ ] サンプルコード追加（`examples/usage_tracking.py`）

---

## 補足情報

### 利点

- デバッグが容易になる（どのトークンがどこで使われたか分かる）
- コスト最適化（cache利用状況を把握）
- パフォーマンス分析

### 制約・リスク

- Claude Code SDKのバージョンによってフィールドが異なる可能性
- Pydantic AIの`Usage`モデルが全てのフィールドをサポートしていない可能性

### 推定工数

1時間

### 参考リンク

- [Anthropic API - Token Counting](https://docs.anthropic.com/en/docs/about-claude/pricing)
- [Pydantic AI - Usage](https://ai.pydantic.dev/api/result/#pydantic_ai.result.Usage)
- Issue #001: 機能差分調査
