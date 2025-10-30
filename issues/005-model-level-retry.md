# [005] Model-level Retry設定

**Status**: Open
**Priority**: Medium
**Labels**: `enhancement`
**Assignee**: (未割当)
**Related Issues**: #001, #004
**GitHub Issue**: (未作成)
**Created**: 2025-10-30
**Updated**: 2025-10-30

---

## 概要

Model-levelで再試行回数を明示的に設定できるようにし、ネットワークエラーや一時的な障害への耐性を向上させる。

---

## 問題・動機

現在、Pydantic AIのデフォルトリトライに依存しているため、Claude Code CLI特有のエラー（CLI起動失敗、プロセスタイムアウト等）に対する細かな制御ができない。

**本家の機能**:
```python
agent = Agent(model, retries=3)  # 再試行回数を明示的に設定
```

---

## 提案

### 実装方針

1. `ClaudeCodeCLIModel`に`retries`パラメータを追加
2. `request()` メソッドでリトライロジックを実装
3. `ClaudeCLIProcessError`の種類に応じて再試行可否を判定
4. 再試行間隔を設定可能にする（exponential backoff）

### 技術的詳細

**修正箇所**:
- `src/pydantic_claude_cli/model.py:81-140` (初期化)
- `src/pydantic_claude_cli/model.py:239-485` (request メソッド)

```python
# モデル初期化に追加
@dataclass(init=False)
class ClaudeCodeCLIModel(Model):
    # 既存のフィールド...
    _retries: int = field(default=3, repr=False)
    _retry_delay: float = field(default=1.0, repr=False)

    def __init__(
        self,
        model_name: str,
        *,
        retries: int = 3,
        retry_delay: float = 1.0,
        # 既存のパラメータ...
    ):
        self._retries = retries
        self._retry_delay = retry_delay
        # 既存の初期化...

# リトライロジック
async def request(
    self,
    messages: list[ModelMessage],
    model_settings: ModelSettings | None,
    model_request_parameters: ModelRequestParameters,
) -> ModelResponse:
    last_error = None

    for attempt in range(self._retries):
        try:
            # 既存のリクエストロジック
            return await self._make_request(messages, ...)

        except ClaudeCLIProcessError as e:
            last_error = e

            # 再試行可能なエラーか判定
            if not self._is_retryable_error(e):
                raise

            # 最後の試行なら例外を投げる
            if attempt == self._retries - 1:
                raise

            # Exponential backoff
            delay = self._retry_delay * (2 ** attempt)
            logger.warning(
                f"Request failed (attempt {attempt + 1}/{self._retries}), "
                f"retrying in {delay}s: {e}"
            )
            await asyncio.sleep(delay)

    # Should not reach here
    raise last_error

def _is_retryable_error(self, error: ClaudeCLIProcessError) -> bool:
    """エラーが再試行可能か判定"""
    retryable_messages = [
        "network error",
        "timeout",
        "connection refused",
        "rate limit",
        "503",
        "502",
    ]
    error_str = str(error).lower()
    return any(msg in error_str for msg in retryable_messages)
```

---

## タスク

- [ ] `ClaudeCodeCLIModel`に`retries`と`retry_delay`パラメータを追加
- [ ] `_is_retryable_error()`メソッドを実装
- [ ] `request()`メソッドにリトライロジックを追加
- [ ] Exponential backoffを実装
- [ ] テストケース追加（`tests/test_model_retry.py`）
  - [ ] 正常ケース（再試行なし）
  - [ ] 再試行可能エラーで再試行成功
  - [ ] max retriesに達してエラー
  - [ ] 再試行不可エラーで即座に失敗
- [ ] ロギングを追加（再試行状況を記録）
- [ ] ドキュメント更新（retry設定の説明）
- [ ] サンプルコード追加（`examples/retry_config.py`）

---

## 補足情報

### 利点

- ネットワークエラーや一時的な障害への耐性向上
- ユーザーが再試行戦略を細かく制御可能
- より堅牢なプロダクション環境での運用

### 制約・リスク

- 再試行回数が多いとレスポンス時間が長くなる
- 一部のエラーは再試行しても解決しない（API key invalid等）
- Claude Code CLIの起動失敗は再試行で解決する可能性が低い

### 再試行すべきエラーの例

**再試行すべき**:
- ネットワークタイムアウト
- 接続エラー（connection refused）
- Rate limit errors (429)
- サーバーエラー (502, 503)
- CLI起動の一時的な失敗

**再試行すべきでない**:
- 認証エラー (401)
- CLI not found (インストールされていない)
- 不正なリクエスト (400)
- リソースが見つからない (404)

### 推定工数

3-4時間

### 参考リンク

- [Pydantic AI - HTTP Request Retries](https://ai.pydantic.dev/retries/)
- [Tenacity Library](https://tenacity.readthedocs.io/) - Pydantic AIが使用している再試行ライブラリ
- Issue #001: 機能差分調査
- Issue #004: Result Validator（関連機能）
