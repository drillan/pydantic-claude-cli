# ユーザーガイド

pydantic-claude-cliの使い方を説明します。

```{contents}
:depth: 2
:local:
```

---

## 基本的な使い方

### インストール

```bash
pip install pydantic-claude-cli
```

### 最小限の例

```python
import asyncio
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

async def main():
    # モデルを作成
    model = ClaudeCodeCLIModel('claude-sonnet-4-5-20250929')

    # Agentを作成
    agent = Agent(model, instructions='簡潔に答えてください。')

    # 実行
    result = await agent.run('こんにちは！')
    print(result.output)

asyncio.run(main())
```

---

## カスタムツールの使い方（v0.2+）

### 基本的なカスタムツール

```python
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

# ステップ1: モデルとAgentを作成
model = ClaudeCodeCLIModel('claude-sonnet-4-5-20250929')
agent = Agent(model)

# ステップ2: toolsetsを設定（重要！）
model.set_agent_toolsets(agent._function_toolset)

# ステップ3: カスタムツールを定義
@agent.tool_plain
def calculate_total(prices: list[float]) -> float:
    """価格リストの合計を計算"""
    return sum(prices)

# ステップ4: 実行
result = await agent.run('100円、200円、300円の合計を計算して')
print(result.output)
```

### サポートされる機能

✅ **基本型のツール**:
- int, str, float, bool, list, dict

✅ **Pydanticモデル**:
```python
from pydantic import BaseModel

class Product(BaseModel):
    name: str
    price: float

@agent.tool_plain
def get_total(items: list[Product]) -> float:
    return sum(item.price for item in items)
```

✅ **非同期ツール**:
```python
@agent.tool_plain
async def async_process(data: str) -> str:
    import asyncio
    await asyncio.sleep(0.1)
    return data.upper()
```

### RunContext依存ツールのサポート状況

#### 基本機能（v0.2+）

**`@agent.tool_plain`（依存性なし）のみサポート**:

```python
# ✅ サポート対象
@agent.tool_plain
def calculate(x: int, y: int) -> int:
    return x + y

# ❌ 未サポート（基本機能）
from pydantic_ai.tools import RunContext

@agent.tool
async def query_db(ctx: RunContext[DB], id: int) -> str:
    return await ctx.deps.query(id)
```

#### 実験的機能（v0.2+）

**シリアライズ可能な依存性のみサポート（実験的）**:

```python
from pydantic_ai import RunContext
from pydantic_claude_cli import ClaudeCodeCLIAgent, ClaudeCodeCLIModel

# ✅ 実験的機能でサポート
model = ClaudeCodeCLIModel('...', enable_experimental_deps=True)
agent = ClaudeCodeCLIAgent(model, deps_type=dict)
model.set_agent_toolsets(agent._function_toolset)

@agent.tool
async def get_config(ctx: RunContext[dict], key: str) -> str:
    return ctx.deps.get(key, "not found")

result = await agent.run("Get API key", deps={"api_key": "abc"})
```

**詳細**: [実験的依存性サポート](experimental-deps.md)

#### Pydantic AI標準でのサポート

**すべての機能が必要な場合**:

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

# Pydantic AI標準（API key必要）
model = AnthropicModel('claude-sonnet-4-5-20250929', api_key='...')
agent = Agent(model, deps_type=httpx.AsyncClient)

@agent.tool
async def fetch(ctx: RunContext[httpx.AsyncClient], url: str) -> str:
    response = await ctx.deps.get(url)  # ✅ すべての機能をサポート
    ctx.retry("Retrying...")  # ✅ すべての機能をサポート
    return response.text
```

---

## エラーハンドリング

### CLI未検出エラー

```python
from pydantic_claude_cli import ClaudeCLINotFoundError

try:
    model = ClaudeCodeCLIModel('claude-sonnet-4-5-20250929')
    agent = Agent(model)
    result = await agent.run('Hello')
except ClaudeCLINotFoundError:
    print('Claude CLIをインストールしてください')
    print('npm install -g @anthropic-ai/claude-code')
```

### プロセスエラー

```python
from pydantic_claude_cli import ClaudeCLIProcessError

try:
    result = await agent.run('...')
except ClaudeCLIProcessError as e:
    print(f'CLIエラー: {e}')
```

---

## トラブルシューティング

### CLIが見つからない

**症状**: `ClaudeCLINotFoundError`

**解決方法**:
```bash
# Claude Code CLIをインストール
npm install -g @anthropic-ai/claude-code

# 確認
claude --version
```

### ログインが必要

**症状**: 認証エラー

**解決方法**:
```bash
claude login
```

### カスタムツールが動作しない

**症状**: ツールが呼び出されない

**確認事項**:
1. `model.set_agent_toolsets(agent._function_toolset)` を呼び出したか
2. `@agent.tool_plain` を使用しているか（`@agent.tool`ではない）
3. RunContextを使用していないか

**デバッグ**:
```python
import warnings
warnings.simplefilter("always")  # 警告を表示

# 実行すると、MCPサーバー作成のログが表示される
result = await agent.run('...')
```

---

## サンプルコード

詳細なサンプルは`examples/`ディレクトリを参照：

- `basic_usage.py` - 基本的な使い方
- `error_handling.py` - エラーハンドリング
- `custom_tools_basic.py` - カスタムツール基本
- `custom_tools_advanced.py` - カスタムツール高度な例

---

## 次のステップ

- [動作の仕組み](how-it-works.md) - 内部動作の理解
- [アーキテクチャ](architecture.md) - システム設計
- [カスタムツール](custom-tools.md) - ツールの詳細説明
