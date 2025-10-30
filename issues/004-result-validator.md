# [004] Result Validatorのサポート

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

Pydantic AIの`@agent.result_validator`機能をサポートし、応答品質の自動検証と再試行を可能にする。

---

## 問題・動機

現在、Result Validatorが未サポートのため、応答品質の自動検証ができない。本家Pydantic AIでは、`ModelRetry`例外を使って応答を検証し、不適切な応答を再生成できる。

**本家の機能**:
```python
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelRetry

agent = Agent(model)

@agent.result_validator
async def validate_response(ctx: RunContext, result: str) -> str:
    if len(result) < 10:
        raise ModelRetry('Response too short, please provide more detail')
    if 'inappropriate_word' in result.lower():
        raise ModelRetry('Response contains inappropriate content')
    return result
```

---

## 提案

### 実装方針

1. Pydantic AIのAgent側が既に`result_validator`をサポートしているか確認
2. Model側で`ModelRetry`例外を適切にハンドリング
3. 再試行ロジックを実装（max retriesに達するまで）
4. テストケースを追加して動作確認

### 技術的詳細

**調査が必要**:
- Pydantic AIの`Agent`がどのようにResult Validatorを呼び出すか
- Model側で特別な対応が必要か、それともAgentが自動的に処理するか

**可能性1: Agent側で完全にサポート済み**
- Model側は何もしなくても動作する可能性
- その場合、テストケースを追加するだけで良い

**可能性2: Model側で再試行ロジックが必要**
```python
# model.py の request() メソッド内
async def request(
    self,
    messages: list[ModelMessage],
    model_settings: ModelSettings | None,
    model_request_parameters: ModelRequestParameters,
) -> ModelResponse:
    # 現在の実装...

    # 再試行ロジックを追加する必要があるかもしれない
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 既存のロジック
            response = await self._make_request(...)
            return response
        except ModelRetry as e:
            if attempt == max_retries - 1:
                raise
            # リトライメッセージをプロンプトに追加
            messages.append(RetryPromptPart(content=str(e)))
            continue
```

---

## タスク

- [ ] Pydantic AIの`result_validator`実装を調査
  - [ ] Agent側の処理フローを確認
  - [ ] Model側で必要な対応を特定
- [ ] Model側で`ModelRetry`例外のハンドリングを実装（必要な場合）
- [ ] 再試行ロジックを実装（必要な場合）
- [ ] テストケース追加（`tests/test_result_validator.py`）
  - [ ] 基本的なvalidation成功ケース
  - [ ] ModelRetryによる再試行ケース
  - [ ] max retriesに達した場合のエラーケース
- [ ] ドキュメント更新（Result Validatorの使用例）
- [ ] サンプルコード追加（`examples/result_validator.py`）

---

## 補足情報

### 利点

- 応答品質の自動検証
- 不適切な応答の自動再試行
- より堅牢なアプリケーション

### 制約・リスク

- Pydantic AI側の実装に依存する
- 再試行回数が多いとコストが増加
- Claude Code CLIが再試行をサポートしているか確認が必要

### 推定工数

2-3時間（調査を含む）

### 参考リンク

- [Pydantic AI - Result Validators](https://ai.pydantic.dev/api/result/)
- [Pydantic AI - ModelRetry Exception](https://ai.pydantic.dev/api/exceptions/)
- Issue #001: 機能差分調査
