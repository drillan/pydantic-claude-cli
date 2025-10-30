# [001] 本家Pydantic AIとの機能差分調査：実装が容易な未実装機能の提案

**Status**: Open
**Priority**: High
**Labels**: `enhancement`, `documentation`, `help wanted`
**Assignee**: (未割当)
**Related Issues**: (なし)
**GitHub Issue**: (未作成)
**Created**: 2025-10-30
**Updated**: 2025-10-30

---

## 概要

本家のPydantic AIとこのプロジェクト（pydantic-claude-cli）の機能差分を調査し、実装が容易な未実装機能を特定しました。

**現在の機能カバレッジ**: 約60%
**目標**: 70-75%（以下の機能を実装することで達成可能）

---

## 実装が容易な未実装機能（推奨順）

### 1. ModelSettingsの完全サポート 🟢 容易度: 低

**現状**: 基本的なModelSettingsは受け取るが、`temperature`、`max_tokens`、`top_p`等のパラメータが`ClaudeCodeOptions`に渡されていない

**本家の機能**:
```python
agent = Agent(
    model,
    model_settings={
        'temperature': 0.7,
        'max_tokens': 1000,
        'top_p': 0.9
    }
)
```

**実装方針**:
- `model.py:239` の `request()` メソッド内で`model_settings`を解析
- `ClaudeCodeOptions`にパラメータを追加（Claude Code SDKが対応している場合）
- 対応パラメータのマッピング処理を追加

**利点**: ユーザーがモデルの振る舞いを細かく制御できる

**推定工数**: 1-2時間

---

### 2. Usage情報の詳細化 🟢 容易度: 低

**現状**: 基本的なtoken countとcostは取得済みだが、詳細メトリクスが未活用

**本家の機能**: より詳細な使用状況トラッキング

**実装方針**:
- `message_converter.py:147` の `extract_usage_from_result()` を拡張
- `result_message.usage` から詳細情報を抽出（cache hits, thinking tokens等）
- `ModelResponse.usage` に追加情報を含める

**利点**: デバッグやコスト管理が容易になる

**推定工数**: 1時間

---

### 3. Result Validatorのサポート 🟡 容易度: 中

**現状**: 未実装

**本家の機能**:
```python
from pydantic_ai import Agent

agent = Agent(model)

@agent.result_validator
async def validate_response(ctx: RunContext, result: str) -> str:
    if len(result) < 10:
        raise ModelRetry('Response too short')
    return result
```

**実装方針**:
- Pydantic AIのAgent側が既にサポートしているため、Model側は特別な対応不要かも
- `ModelRetry`例外を適切にハンドリング（再試行ロジック）
- テストケースを追加して動作確認

**利点**: 応答品質の自動検証と再試行

**推定工数**: 2-3時間

---

### 4. Model-level Retry設定 🟡 容易度: 中

**現状**: Pydantic AIのデフォルトリトライに依存

**本家の機能**:
```python
agent = Agent(model, retries=3)  # 再試行回数を明示的に設定
```

**実装方針**:
- `ClaudeCodeCLIModel`に`retries`パラメータを追加
- `request()` メソッドでリトライロジックを実装
- `ClaudeCLIProcessError`の種類に応じて再試行可否を判定

**利点**: ネットワークエラーや一時的な障害への耐性向上

**推定工数**: 3-4時間

---

### 5. Tool Error Handling の改善 🟡 容易度: 中

**現状**: ツールエラーが汎用的な`ClaudeCLIProcessError`でラップされる

**本家の機能**: ツールエラーを構造化して、LLMが適切に対応できる

**実装方針**:
- `tool_converter.py` または `mcp_server_fixed.py` でツール実行エラーをキャッチ
- エラー情報を構造化してLLMに返す（エラーメッセージ、スタックトレース等）
- ToolReturnPartにエラー情報を含める

**利点**: LLMがツールエラーから学習し、修正を試みることができる

**推定工数**: 3-4時間

---

## 実装が難しい機能（参考）

以下は実装が難しく、短期的には推奨しません：

- ❌ **Streaming**: Claude Code SDKのストリーミング対応が不明、大きなアーキテクチャ変更が必要
- ❌ **Multimodal (画像・ファイル)**: CLI経由での画像処理が未対応
- ❌ **Output tools / Structured output**: 構造化出力の処理が複雑
- ❌ **Full RunContext support**: `ctx.retry()`, `ctx.run_step()` 等のCLI側の制約

---

## 推奨実装順序

1. **ModelSettings完全サポート** (1-2時間) - ユーザー体験向上、実装簡単
2. **Usage情報詳細化** (1時間) - デバッグ・運用改善
3. **Result Validator** (2-3時間) - 品質向上、既存機能との統合確認が必要
4. **Retry設定** (3-4時間) - 信頼性向上

---

## 補足情報

### 現在の実装状況まとめ

**実装済み（✅）**:
- テキストベースの会話
- システムプロンプト
- カスタムツール（@agent.tool_plain）
- 組み込みツール制御（ToolPreset）
- 実験的依存性サポート（シリアライズ可能な型のみ）

**未実装（❌）**:
- ストリーミング応答
- マルチモーダル（画像・ファイル）
- Output tools
- 完全なRunContextサポート
- Result validators
- Model-level retry設定

### 参考リンク

- [Pydantic AI公式ドキュメント](https://ai.pydantic.dev/)
- [Pydantic AI - Result Validators](https://ai.pydantic.dev/api/result/)
- [Pydantic AI - HTTP Request Retries](https://ai.pydantic.dev/retries/)

---

## アクションアイテム

これらの機能を個別のissueに分割し、実装を進めることを提案します。各機能について：

- [ ] ModelSettingsの完全サポート
- [ ] Usage情報の詳細化
- [ ] Result Validatorのサポート
- [ ] Model-level Retry設定
- [ ] Tool Error Handlingの改善
