# [006] Tool Error Handlingの改善

**Status**: Open
**Priority**: Medium
**Labels**: `enhancement`, `tools`
**Assignee**: (未割当)
**Related Issues**: #001
**GitHub Issue**: (未作成)
**Created**: 2025-10-30
**Updated**: 2025-10-30

---

## 概要

ツールエラーを構造化してLLMに返すことで、LLMがエラーから学習し、修正を試みることができるようにする。

---

## 問題・動機

現在、ツールエラーが汎用的な`ClaudeCLIProcessError`でラップされるため、LLMがエラーの詳細を理解できず、適切な対応ができない。

**現在の動作**:
```python
@agent.tool_plain
def divide(a: int, b: int) -> float:
    return a / b  # b=0の場合、ZeroDivisionErrorが発生

# エラーが発生すると、LLMには詳細が伝わらない
```

**理想的な動作**:
```python
# エラーが構造化されてLLMに返される
{
    "error": "ZeroDivisionError",
    "message": "division by zero",
    "traceback": "...",
    "tool_name": "divide",
    "arguments": {"a": 10, "b": 0}
}

# LLMは次のように対応できる
"I see that dividing by zero caused an error. Let me try with a different value..."
```

---

## 提案

### 実装方針

1. `tool_converter.py` または `mcp_server_fixed.py` でツール実行エラーをキャッチ
2. エラー情報を構造化（エラータイプ、メッセージ、スタックトレース）
3. `ToolReturnPart`にエラー情報を含める
4. LLMが理解しやすい形式でエラーメッセージを整形

### 技術的詳細

**修正箇所**:
- `src/pydantic_claude_cli/tool_converter.py:244` (create_mcp_from_tools)
- `src/pydantic_claude_cli/mcp_server_fixed.py` (ツール実行部分)

```python
# mcp_server_fixed.py のツール実行部分

async def execute_tool(tool_name: str, arguments: dict) -> dict:
    """ツールを実行し、エラーをハンドリング"""
    try:
        # 既存のツール実行ロジック
        result = await tool_func(**arguments)
        return {"success": True, "result": result}

    except Exception as e:
        # エラーを構造化
        import traceback
        error_info = {
            "success": False,
            "error": {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc(),
                "tool_name": tool_name,
                "arguments": arguments,
            }
        }

        # LLM向けにフォーマット
        formatted_error = format_error_for_llm(error_info)
        logger.error(f"Tool execution error: {formatted_error}")

        return error_info

def format_error_for_llm(error_info: dict) -> str:
    """LLMが理解しやすい形式にエラーをフォーマット"""
    error = error_info["error"]
    return (
        f"Tool '{error['tool_name']}' failed with {error['type']}: {error['message']}\n"
        f"Arguments: {error['arguments']}\n"
        f"Please try a different approach or correct the arguments."
    )
```

**考慮事項**:
- スタックトレースは詳細すぎる可能性（トークン消費）
- セキュリティ：機密情報がエラーメッセージに含まれないようにする
- ユーザーが独自のエラーハンドリングを実装できるようにする

---

## タスク

- [ ] ツール実行エラーのキャッチメカニズムを実装
- [ ] エラー構造化ロジックを実装
- [ ] `format_error_for_llm()`を実装
- [ ] セキュリティチェック（機密情報の除外）
- [ ] テストケース追加（`tests/test_tool_error_handling.py`）
  - [ ] 正常なツール実行
  - [ ] ZeroDivisionErrorのハンドリング
  - [ ] TypeErrorのハンドリング
  - [ ] カスタム例外のハンドリング
  - [ ] LLMが再試行できることを確認
- [ ] ロギング改善（エラー詳細を記録）
- [ ] ドキュメント更新（エラーハンドリングの説明）
- [ ] サンプルコード追加（`examples/tool_error_handling.py`）

---

## 補足情報

### 利点

- LLMがエラーから学習し、修正を試みることができる
- デバッグが容易になる（詳細なエラー情報）
- より堅牢なツール統合

### 制約・リスク

- スタックトレースが長すぎるとトークン消費が増える
- 機密情報がエラーメッセージに含まれる可能性
- MCP Server側の実装に依存する

### エラーフォーマットの例

**簡潔版**（推奨）:
```
Tool 'divide' failed: Cannot divide by zero (ZeroDivisionError)
Arguments: {"a": 10, "b": 0}
Suggestion: Please use a non-zero divisor.
```

**詳細版**（デバッグ用）:
```json
{
  "tool": "divide",
  "error_type": "ZeroDivisionError",
  "message": "division by zero",
  "arguments": {"a": 10, "b": 0},
  "traceback": "Traceback (most recent call last):\n  File ...",
  "timestamp": "2025-10-30T12:00:00Z"
}
```

### 推定工数

3-4時間

### 参考リンク

- [Pydantic AI - Tools](https://ai.pydantic.dev/tools/)
- [MCP Server Specification](https://github.com/anthropics/mcp)
- Issue #001: 機能差分調査
