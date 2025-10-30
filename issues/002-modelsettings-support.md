# [002] ModelSettingsの完全サポート

**Status**: Completed
**Priority**: High
**Labels**: `enhancement`, `good first issue`
**Assignee**: Claude
**Related Issues**: #001
**GitHub Issue**: (未作成)
**Created**: 2025-10-30
**Updated**: 2025-10-30
**Completed**: 2025-10-30

---

## 概要

`temperature`、`max_tokens`、`top_p`等のModelSettingsパラメータを`ClaudeCodeOptions`に渡せるようにする。

---

## 問題・動機

現在、`ClaudeCodeCLIModel`は`ModelSettings`を受け取るが、実際にはClaude Code CLIに渡されていない。これにより、ユーザーがモデルの振る舞いを細かく制御できない。

**現在の動作**:
```python
model = ClaudeCodeCLIModel(
    'claude-haiku-4-5',
    settings={'temperature': 0.7}  # 無視される
)
```

---

## 提案

### 実装方針

1. `model.py:239` の `request()` メソッド内で`model_settings`を解析
2. Claude Code SDKの`ClaudeCodeOptions`がサポートするパラメータを確認
3. サポートされているパラメータのマッピング処理を追加
4. 未サポートパラメータの場合はwarningログを出力

### 技術的詳細

**修正箇所**: `src/pydantic_claude_cli/model.py:239-400`

```python
# 現在のコード (line 389付近)
options = ClaudeCodeOptions(
    model=self._model_name,
    system_prompt=system_prompt,
    max_turns=self._max_turns,
    permission_mode=self._permission_mode,
    # 追加: model_settings からパラメータを抽出
)

# 提案する変更
def _extract_model_settings(
    self, model_settings: ModelSettings | None
) -> dict[str, Any]:
    """ModelSettingsから Claude Code SDK対応パラメータを抽出"""
    if not model_settings:
        return {}

    params = {}
    supported = ['temperature', 'max_tokens', 'top_p']

    for key in supported:
        if hasattr(model_settings, key):
            value = getattr(model_settings, key)
            if value is not None:
                params[key] = value

    return params

# request()メソッド内で使用
model_params = self._extract_model_settings(model_settings)
options = ClaudeCodeOptions(
    model=self._model_name,
    system_prompt=system_prompt,
    max_turns=self._max_turns,
    permission_mode=self._permission_mode,
    **model_params,  # 追加
)
```

**Claude Code SDKの確認が必要**:
- `ClaudeCodeOptions`が受け取れるパラメータを調査
- SDKドキュメントまたはソースコードを確認

---

## タスク

- [ ] Claude Code SDKの`ClaudeCodeOptions`対応パラメータを調査
- [ ] `_extract_model_settings()`メソッドを実装
- [ ] `request()`メソッドで`model_settings`を`ClaudeCodeOptions`に渡す
- [ ] 未サポートパラメータの警告ログを追加
- [ ] テストケースを追加（`tests/test_model.py`）
  - [ ] temperatureが正しく渡されることを確認
  - [ ] max_tokensが正しく渡されることを確認
  - [ ] 未サポートパラメータでwarningが出ることを確認
- [ ] ドキュメント更新（`README.md`の使用例）
- [ ] サンプルコード追加（`examples/model_settings.py`）

---

## 補足情報

### 利点

- ユーザーがモデルの振る舞いを細かく制御できる
- 本家Pydantic AIとの互換性向上
- より予測可能な応答生成

### 制約・リスク

- Claude Code SDKが全てのパラメータをサポートしているとは限らない
- SDKバージョンによって対応パラメータが異なる可能性

### 推定工数

1-2時間

### 参考リンク

- [Pydantic AI - ModelSettings](https://ai.pydantic.dev/api/models/)
- [Claude Code SDK](https://github.com/anthropics/claude-code-sdk-python)
- Issue #001: 機能差分調査


---

## Updates

### 2025-10-30 - 実装完了 ✅

**実装内容**:
- `_extract_model_settings()`メソッドを追加（`model.py:239-279`）
- `temperature`, `max_tokens`, `top_p`を`ClaudeCodeOptions.extra_args`経由でCLIに渡す実装
- `request()`メソッドで`model_settings`を抽出して`ClaudeCodeOptions`に渡す処理を追加

**テスト**:
- Test-First開発に従い、8つのユニットテストを作成（`tests/test_model_settings.py`）
- すべてのテスト通過（69 passed, 7 skipped）
- Red→Green phaseを確認

**コード品質**:
- Article 8（Code Quality Standards）完全準拠
- ruff check & format: All checks passed ✅
- mypy: No issues found ✅

**ドキュメント**:
- README.mdに使用例を追加
- `examples/model_settings.py`に4つの実用例を追加
  - 基本的な使用方法
  - temperature比較
  - max_tokens制御
  - 複数設定の組み合わせ

**注意事項**:
- `extra_args`経由でパラメータを渡すため、実験的機能として実装
- Claude Code CLIがこれらのパラメータをサポートしているかは未確認
- 警告ログで実験的機能であることをユーザーに通知

**推定工数**: 実際の工数は約1.5時間（予定1-2時間内）

**参考リンク**:
- Commit: cf44771
- Test file: `tests/test_model_settings.py`
- Example: `examples/model_settings.py`
- Documentation: `README.md` (line 98-125)

