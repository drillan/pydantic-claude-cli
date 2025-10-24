# pydantic-claude-cli ドキュメント

`pydantic-claude-cli` は、Pydantic AI 用の Claude Code CLI アダプターです。
APIキー不要で Claude モデルにアクセスできます。

## 概要

このライブラリは、Claude Code CLI を介して Anthropic の Claude モデルにアクセスするための
Pydantic AI モデルプロバイダーを提供します。

**主な特徴:**

- ✅ **APIキー不要**: Claude Code CLI が認証を処理
- ✅ **シームレスな統合**: Pydantic AI の標準インターフェースを実装
- ✅ **簡単なセットアップ**: `claude login` だけで使用開始
- ✅ **カスタムツールサポート**: 依存性なしツールが完全動作（v0.2+）

## ドキュメント

```{toctree}
:caption: ユーザーガイド
:maxdepth: 2

user-guide
custom-tools
logging
comparison-with-pydantic-ai
```

```{toctree}
:caption: 技術リファレンス
:maxdepth: 1

how-it-works
architecture
```

## クイックスタート

### インストール

```bash
pip install pydantic-claude-cli
```

### 基本的な使い方

```python
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

# モデルを作成
model = ClaudeCodeCLIModel('claude-sonnet-4-5-20250929')

# エージェントを作成
agent = Agent(model, system_prompt='あなたは親切なアシスタントです。')

# 実行
result = await agent.run('こんにちは！')
print(result.data)
```

### カスタムツールの使用（v0.2+）

依存性なしツール（`@agent.tool_plain`）が**完全に動作します**：

```python
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

model = ClaudeCodeCLIModel('claude-sonnet-4-5-20250929')
agent = Agent(model)

# 重要: toolsetsを設定（必須）
model.set_agent_toolsets(agent._function_toolset)

# カスタムツールを定義
@agent.tool_plain
def calculate_total(prices: list[float]) -> float:
    """価格リストの合計を計算"""
    return sum(prices)

@agent.tool_plain
def format_currency(amount: float, currency: str = "JPY") -> str:
    """金額を通貨形式でフォーマット"""
    return f"{amount:,.0f} {currency}"

# 実行
result = await agent.run('100円、200円、300円の合計を計算して、通貨形式で表示して')
print(result.data)
# → "600 JPY"
```

**制限事項**:
- Phase 1では依存性なしツール（`@agent.tool_plain`）のみサポート
- `RunContext`を使用するツール（`@agent.tool`）は未サポート
- 詳細は [カスタムツールの詳細](custom-tools-explained.md) を参照

## リンク

- [GitHub リポジトリ](https://github.com/yourusername/pydantic-claude-cli)
- [PyPI パッケージ](https://pypi.org/project/pydantic-claude-cli/)
- [Pydantic AI](https://ai.pydantic.dev/)
- [Claude Code CLI](https://docs.anthropic.com/claude/docs/claude-code)
