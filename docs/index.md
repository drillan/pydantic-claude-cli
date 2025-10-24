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

## ドキュメント

```{toctree}
:caption: 目次
:maxdepth: 2

how-it-works
architecture
comparison-with-pydantic-ai
custom-tools-explained
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

## リンク

- [GitHub リポジトリ](https://github.com/yourusername/pydantic-claude-cli)
- [PyPI パッケージ](https://pypi.org/project/pydantic-claude-cli/)
- [Pydantic AI](https://ai.pydantic.dev/)
- [Claude Code CLI](https://docs.anthropic.com/claude/docs/claude-code)
