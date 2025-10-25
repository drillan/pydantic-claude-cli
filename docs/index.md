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
- ✅ **カスタムツールサポート**:
  - 依存性なしツール（v0.2+）
  - 実験的依存性サポート（v0.2+、シリアライズ可能な依存性のみ）
- ✅ **組み込みツール制御**（v0.3+）:
  - WebSearch、Edit、Read等を柔軟に制御
  - ToolPresetとBuiltinTools定数で型安全に設定

## ドキュメント

```{toctree}
:caption: ユーザーガイド
:maxdepth: 2

user-guide
custom-tools
experimental-deps
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
model = ClaudeCodeCLIModel('claude-haiku-4-5')

# エージェントを作成
agent = Agent(model, system_prompt='あなたは親切なアシスタントです。')

# 実行
result = await agent.run('こんにちは！')
print(result.data)
```

### カスタムツールの使用（v0.2+）

依存性なしツール（`@agent.tool_plain`）がサポートされています（v0.2+）：

```python
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

model = ClaudeCodeCLIModel('claude-haiku-4-5')
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

**機能レベル**:
- **基本機能（v0.2+）**: 依存性なしツール（`@agent.tool_plain`）✅
- **実験的機能（v0.2+）**: RunContext依存ツール（`@agent.tool`）⚠️
  - シリアライズ可能な依存性のみ（dict, Pydanticモデル, dataclass）
  - 詳細は [実験的依存性サポート](experimental-deps.md) を参照

**詳細ガイド**:
- [カスタムツール](custom-tools.md) - 基本機能のガイド
- [実験的依存性サポート](experimental-deps.md) - 実験的機能の使い方

### 組み込みツールの制御（v0.3+）

Claude Code CLIの組み込みツール（WebSearch、Edit、Read等）を柔軟に制御できます：

```python
from pydantic_claude_cli import ClaudeCodeCLIModel, ToolPreset

# Web検索を有効化
model = ClaudeCodeCLIModel(
    'claude-sonnet-4-5-20250929',
    tool_preset=ToolPreset.WEB_ENABLED,
    permission_mode='acceptEdits'
)
agent = Agent(model)

# WebSearchが使える
result = await agent.run('最新の情報を教えてください')
```

**利用可能なプリセット**:
- `ToolPreset.WEB_ENABLED` - WebSearch + WebFetch
- `ToolPreset.READ_ONLY` - Read + Glob + Grep
- `ToolPreset.SAFE` - 読み込み + Web（Bashなし）
- `ToolPreset.ALL` - すべての組み込みツール

**詳細**: [ユーザーガイド - 組み込みツールの制御](user-guide.md)

## リンク

- [GitHub リポジトリ](https://github.com/yourusername/pydantic-claude-cli)
- [PyPI パッケージ](https://pypi.org/project/pydantic-claude-cli/)
- [Pydantic AI](https://ai.pydantic.dev/)
- [Claude Code CLI](https://docs.anthropic.com/claude/docs/claude-code)
