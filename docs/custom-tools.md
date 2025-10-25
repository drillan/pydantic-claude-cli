# カスタムツール

pydantic-claude-cli v0.2+では、カスタムツール（ユーザー定義の関数）を使用できます。

```{contents}
:depth: 2
:local:
```

---

## クイックスタート

### 基本的な使い方

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
def calculate_sum(numbers: list[float]) -> float:
    """数値リストの合計を計算"""
    return sum(numbers)

# ステップ4: 実行
result = await agent.run('100, 200, 300の合計を計算して')
print(result.output)
# → ツールが呼び出され、正しい結果が返る
```

**重要**: `model.set_agent_toolsets(agent._function_toolset)` の呼び出しを忘れないでください。

---

## サポートされる機能

### 基本型のツール

```python
@agent.tool_plain
def add(x: int, y: int) -> int:
    """2つの数値を足す"""
    return x + y

@agent.tool_plain
def format_text(text: str, uppercase: bool = False) -> str:
    """テキストをフォーマット"""
    return text.upper() if uppercase else text.lower()
```

### Pydanticモデルを使ったツール

```python
from pydantic import BaseModel

class Product(BaseModel):
    name: str
    price: float
    quantity: int = 1

@agent.tool_plain
def calculate_order_total(products: list[Product]) -> float:
    """注文合計を計算"""
    return sum(p.price * p.quantity for p in products)
```

### 非同期ツール

```python
@agent.tool_plain
async def fetch_data(url: str) -> str:
    """URLからデータを取得"""
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text
```

### 複数ツールの連携

LLMが自動的に複数のツールを順番に呼び出します：

```python
@agent.tool_plain
def add(x: int, y: int) -> int:
    return x + y

@agent.tool_plain
def multiply(x: int, y: int) -> int:
    return x * y

# LLMが add → multiply の順で呼び出す
result = await agent.run('(5 + 3) × 2 を計算して')
# 1. add(5, 3) = 8
# 2. multiply(8, 2) = 16
```

---

## 制限事項

### RunContext依存ツール

**基本機能（v0.2+）**: 依存性なしツール（`@agent.tool_plain`）のみサポート

**実験的機能（v0.2+）**: シリアライズ可能な依存性のみサポート

```python
from pydantic_ai.tools import RunContext

# ❌ 基本機能では未サポート
@agent.tool
async def get_user(ctx: RunContext[Database], user_id: int) -> str:
    # ctx.depsにアクセスできない
    return await ctx.deps.query_user(user_id)

# ✅ 実験的機能でサポート（シリアライズ可能な依存性）
@agent.tool
async def get_config(ctx: RunContext[dict], key: str) -> str:
    return ctx.deps.get(key, "not found")
```

**回避策**:
1. **実験的依存性サポートを使用**（v0.2+）
   - [実験的依存性サポート](experimental-deps.md)を参照
   - シリアライズ可能な依存性（dict, Pydanticモデル等）のみサポート
   - `ClaudeCodeCLIAgent` + `enable_experimental_deps=True`が必要

2. **Pydantic AI標準を使用**
   - AnthropicModelを使用（API key必要）
   - すべてのRunContext機能をサポート

3. **依存性を引数として明示的に渡す**

### set_agent_toolsetsの手動呼び出しが必要

現在は、Agent作成後に手動で設定する必要があります：

```python
model = ClaudeCodeCLIModel('...')
agent = Agent(model)
model.set_agent_toolsets(agent._function_toolset)  # 必須
```

---

## トラブルシューティング

### ツールが呼び出されない

**確認事項**:

1. `model.set_agent_toolsets(agent._function_toolset)` を呼び出したか？

2. `@agent.tool_plain` を使用しているか？
   - ❌ `@agent.tool` （RunContext依存）
   - ✅ `@agent.tool_plain` （依存性なし）

3. デバッグログを確認:
   ```python
   import warnings
   warnings.simplefilter("always")

   result = await agent.run('...')
   # "Creating FIXED MCP server with N tools" が表示されるはず
   ```

### エラー: "Tool function not found"

**原因**: `set_agent_toolsets()`が呼び出されていない

**解決策**:
```python
model.set_agent_toolsets(agent._function_toolset)
```

---

## サンプルコード

詳細なサンプルは`examples/`ディレクトリを参照：

### 基本機能（v0.2+）

- **`custom_tools_basic.py`** - 基本的な使い方
  - シンプルな計算ツール
  - 複数ツールの連携
  - 通貨フォーマット

- **`custom_tools_advanced.py`** - 高度な使い方
  - Pydanticモデルを使ったツール
  - 非同期ツール
  - 複雑なデータ処理

### 実験的機能（v0.2+）

- **`experimental_deps_basic.py`** - 基本的な依存性の使い方
  - dict型の依存性
  - 設定値の取得
  - 複数ツールでの依存性共有

- **`experimental_deps_advanced.py`** - 高度な依存性の使い方
  - Pydanticモデルの依存性
  - dataclassの依存性
  - 接続の再作成パターン

すべてのサンプルは動作確認済みです。

---

## 技術的な詳細

実装の詳細、技術的な制約、開発プロセスについては、以下を参照してください：

- [動作の仕組み](how-it-works.md) - 内部動作の詳細
- [アーキテクチャ](architecture.md) - システム設計

---

## よくある質問

### Q: Pydantic AI標準との違いは？

A: カスタムツールの依存性サポートレベルが異なります：

| 機能 | Pydantic AI標準 | 基本機能 (v0.2+) | 実験的機能 (v0.2+) |
|------|----------------|-----------------|-------------------|
| 基本型ツール | ✅ | ✅ | ✅ |
| Pydanticモデル | ✅ | ✅ | ✅ |
| 非同期ツール | ✅ | ✅ | ✅ |
| RunContext（シリアライズ可能deps） | ✅ | ❌ | ✅ |
| RunContext（非シリアライズdeps） | ✅ | ❌ | ❌ |
| `ctx.retry()`, `ctx.run_step` | ✅ | ❌ | ❌ |
| APIキー | 必要 | 不要 | 不要 |

詳細な比較: [Pydantic AI標準との比較](comparison-with-pydantic-ai.md)

### Q: なぜset_agent_toolsets()が必要？

A: Pydantic AIの内部APIの制限により、Modelレイヤーでツール実行関数にアクセスするために必要です。将来のバージョンで自動化を検討しています。

### Q: RunContext依存ツールはサポートされている？

A: **実験的機能としてサポートされています**（v0.2+）

**サポート内容**:
- ✅ **シリアライズ可能な依存性**: dict, Pydanticモデル, dataclass
- ✅ **`ctx.deps`へのアクセス**: 依存性の値を取得可能
- ❌ **非シリアライズ可能な依存性**: httpx, DB接続等は未サポート
- ❌ **RunContextのすべての機能**: `ctx.retry()`, `ctx.run_step`等は未サポート

**使い方**: [実験的依存性サポート](experimental-deps.md)

**RunContextのすべての機能が必要な場合**: Pydantic AI標準（AnthropicModel）の使用を推奨します。
