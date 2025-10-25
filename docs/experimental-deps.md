# 実験的依存性サポート

**ステータス**: 実験的機能（安定版候補）
**バージョン**: v0.2+ (Milestone 3)
**動作確認**: ✅ 完了（85テスト合格、E2E動作確認済み）
**推奨用途**: プロトタイプ、開発環境、非本番環境

pydantic-claude-cli v0.2+では、実験的機能として依存性注入（RunContext + deps）をサポートします。

この機能は完全に動作していますが、以下の理由で実験的機能としています：

1. **Pydantic AI公式APIではなく回避策を使用**
   - ContextVarによる依存性転送
   - 将来的にPydantic AI側でより良い解決策が出る可能性

2. **ユーザーフィードバックに基づいて改善予定**
   - 実際のユースケースでの検証が必要
   - 改善点の発見と対応

3. **制限事項が存在**
   - シリアライズ可能な依存性のみ
   - EmulatedRunContext（完全なRunContextではない）

**安定版への移行予定**: ユーザーフィードバック収集後（約1-2ヶ月）

```{contents}
:depth: 2
:local:
```

---

## 概要

### 何ができるか

Pydantic AIの依存性注入機能を使用して、ツール内で設定情報やAPIキーにアクセスできます：

```python
from pydantic import BaseModel
from pydantic_ai import RunContext
from pydantic_claude_cli import ClaudeCodeCLIModel, ClaudeCodeCLIAgent

class Config(BaseModel):
    api_key: str
    timeout: int

model = ClaudeCodeCLIModel(
    'claude-sonnet-4-5-20250929',
    enable_experimental_deps=True  # 実験的機能を有効化
)
agent = ClaudeCodeCLIAgent(model, deps_type=Config)
model.set_agent_toolsets(agent._function_toolset)

@agent.tool
async def get_user(ctx: RunContext[Config], user_id: int) -> str:
    api_key = ctx.deps.api_key  # 依存性にアクセス
    # API呼び出し
    return f"User {user_id}"

result = await agent.run(
    "Get user 123",
    deps=Config(api_key="secret", timeout=30)
)
```

### 制限事項

この機能には以下の制限があります：

1. **シリアライズ可能な依存性のみ**
   - dict, str, int, Pydanticモデル、dataclassのみサポート
   - HTTPクライアントやデータベース接続は非サポート

2. **EmulatedRunContext**
   - `ctx.deps`のみ使用可能
   - `ctx.retry()`, `ctx.run_step`等は未サポート

3. **ClaudeCodeCLIAgent必須**
   - 通常の`Agent`ではなく`ClaudeCodeCLIAgent`を使用

4. **実験的機能フラグ**
   - `enable_experimental_deps=True`が必要

---

## クイックスタート

### 基本的な使い方

```python
from pydantic_ai import RunContext
from pydantic_claude_cli import ClaudeCodeCLIModel, ClaudeCodeCLIAgent

# ステップ1: モデル作成（実験的機能を有効化）
model = ClaudeCodeCLIModel(
    'claude-sonnet-4-5-20250929',
    enable_experimental_deps=True
)

# ステップ2: ClaudeCodeCLIAgentを使用（重要！）
agent = ClaudeCodeCLIAgent(model, deps_type=dict)
model.set_agent_toolsets(agent._function_toolset)

# ステップ3: RunContext依存ツールを定義
@agent.tool
async def get_config(ctx: RunContext[dict], key: str) -> str:
    """設定値を取得"""
    return ctx.deps.get(key, "not found")

# ステップ4: 実行（depsを渡す）
result = await agent.run(
    "Get the API key",
    deps={"api_key": "abc123", "timeout": 30}
)
```

---

## サポートされる依存性

### プリミティブ型とコレクション

```python
# dict
agent = ClaudeCodeCLIAgent(model, deps_type=dict)
result = await agent.run("...", deps={"key": "value"})

# str
agent = ClaudeCodeCLIAgent(model, deps_type=str)
result = await agent.run("...", deps="my_api_key")

# list
agent = ClaudeCodeCLIAgent(model, deps_type=list)
result = await agent.run("...", deps=[1, 2, 3])
```

### Pydanticモデル

```python
from pydantic import BaseModel

class AppConfig(BaseModel):
    api_key: str
    db_url: str
    timeout: int = 30

agent = ClaudeCodeCLIAgent(model, deps_type=AppConfig)

@agent.tool
async def connect_db(ctx: RunContext[AppConfig]) -> str:
    """データベース接続（設定から再作成）"""
    db_url = ctx.deps.db_url
    # 接続を再作成
    return f"Connected to {db_url}"

result = await agent.run(
    "Connect to database",
    deps=AppConfig(api_key="key", db_url="postgresql://localhost/test")
)
```

### dataclass

```python
from dataclasses import dataclass

@dataclass
class ServiceConfig:
    api_endpoint: str
    api_key: str
    retries: int = 3

agent = ClaudeCodeCLIAgent(model, deps_type=ServiceConfig)

@agent.tool
async def call_api(ctx: RunContext[ServiceConfig], path: str) -> str:
    """API呼び出し"""
    endpoint = ctx.deps.api_endpoint
    api_key = ctx.deps.api_key
    # API呼び出し
    return f"GET {endpoint}/{path}"

result = await agent.run(
    "Call /users endpoint",
    deps=ServiceConfig(
        api_endpoint="https://api.example.com",
        api_key="secret"
    )
)
```

---

## サポートされない依存性

### HTTPクライアント

```python
import httpx

# ❌ これは動作しません
agent = ClaudeCodeCLIAgent(model, deps_type=httpx.AsyncClient)

@agent.tool
async def fetch_data(ctx: RunContext[httpx.AsyncClient], url: str) -> str:
    response = await ctx.deps.get(url)  # エラー
    return response.text

# エラー: "Non-serializable dependencies are not supported"
```

**回避策**: 設定のみを渡し、ツール内でクライアントを再作成

```python
# ✅ これは動作します
@dataclass
class HttpConfig:
    base_url: str
    api_key: str

agent = ClaudeCodeCLIAgent(model, deps_type=HttpConfig)

@agent.tool
async def fetch_data(ctx: RunContext[HttpConfig], path: str) -> str:
    """データ取得"""
    import httpx

    # ツール内でクライアントを再作成
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ctx.deps.base_url}/{path}",
            headers={"Authorization": f"Bearer {ctx.deps.api_key}"}
        )
        return response.text

result = await agent.run(
    "Fetch /users",
    deps=HttpConfig(base_url="https://api.example.com", api_key="secret")
)
```

### データベース接続

```python
# ❌ これは動作しません
from sqlalchemy import Engine

agent = ClaudeCodeCLIAgent(model, deps_type=Engine)
```

**回避策**: 接続文字列を渡し、ツール内で接続を再作成

```python
# ✅ これは動作します
@dataclass
class DbConfig:
    db_url: str
    pool_size: int = 10

agent = ClaudeCodeCLIAgent(model, deps_type=DbConfig)

@agent.tool
async def query_users(ctx: RunContext[DbConfig], limit: int) -> str:
    """ユーザークエリ"""
    from sqlalchemy import create_engine, text

    # ツール内でエンジンを再作成
    engine = create_engine(ctx.deps.db_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM users LIMIT :limit"), {"limit": limit})
        return str(list(result))

result = await agent.run(
    "Query 10 users",
    deps=DbConfig(db_url="postgresql://localhost/mydb")
)
```

---

## トラブルシューティング

### エラー: "Non-serializable dependencies"

**原因**: httpx.AsyncClient、sqlalchemy.Engine等の非シリアライズ可能な依存性を使用

**解決策**:
1. 設定情報のみを依存性として渡す
2. ツール内で接続を再作成する

### エラー: "has no attribute 'retry'"

**原因**: EmulatedRunContextは`ctx.deps`以外のプロパティをサポートしていない

**解決策**:
1. `ctx.retry()`等は使用しない
2. 完全なRunContextが必要な場合、Pydantic AI標準（AnthropicModel）を使用

### エラー: "RunContext tools detected but no deps found"

**原因**: `ClaudeCodeCLIAgent`ではなく通常の`Agent`を使用している

**解決策**:
```python
# ❌ 通常のAgent
from pydantic_ai import Agent
agent = Agent(model, deps_type=dict)

# ✅ ClaudeCodeCLIAgent
from pydantic_claude_cli import ClaudeCodeCLIAgent
agent = ClaudeCodeCLIAgent(model, deps_type=dict)
```

### 依存性が正しく渡されない

**確認事項**:

1. `enable_experimental_deps=True`を設定したか？
2. `ClaudeCodeCLIAgent`を使用しているか？
3. `model.set_agent_toolsets(agent._function_toolset)`を呼び出したか？

---

## セキュリティ注意事項

### 機密情報の取り扱い

依存性にAPI keyやトークンを含める場合、以下に注意してください：

1. **ログ出力**: 依存性はログに出力されません（実装で保証）
2. **メモリクリーンアップ**: ContextVarは自動的にクリーンアップされます
3. **プロセス境界**: In-process MCPサーバーのため、プロセス間通信はありません

### ベストプラクティス

```python
# 機密情報は最小限のスコープで保持
@dataclass
class SecureConfig:
    api_key: str  # 必要最小限の情報のみ

# 接続オブジェクトは含めない
# ❌ client: httpx.AsyncClient  # これは含めない
```

---

## よくある質問

### Q: Pydantic AI標準との違いは？

A: 主な違いは依存性のシリアライズ要件です：

| 機能 | Pydantic AI標準 | pydantic-claude-cli (Milestone 3) |
|------|----------------|-----------------------------------|
| 基本型deps | ✅ | ✅ |
| Pydanticモデルdeps | ✅ | ✅ |
| dataclass deps | ✅ | ✅ |
| HTTPクライアントdeps | ✅ | ❌ |
| データベース接続deps | ✅ | ❌ |
| `ctx.retry()` | ✅ | ❌ |
| `ctx.run_step` | ✅ | ❌ |
| APIキー | 必要 | 不要 |

### Q: なぜシリアライズ可能な依存性のみ？

A: ClaudeCodeCLIModelはCLIプロセスを使用するため、依存性をJSON文字列として転送する必要があります。HTTPクライアントやデータベース接続はJSON化できないため、設定情報のみを渡し、ツール内で再作成します。

### Q: 完全なRunContextサポートはいつ？

A: Pydantic AIのAPIに`Model.request()`への`run_context`パラメータ追加を提案中です。完全なサポートが必要な場合は、Pydantic AI標準（AnthropicModel）の使用を推奨します。

### Q: なぜClaudeCodeCLIAgentが必要？

A: ContextVarに依存性を設定するため、カスタムAgentラッパーが必要です。将来のバージョンで自動化を検討しています。

---

## サンプルコード

詳細なサンプルは`examples/`ディレクトリを参照：

- **`experimental_deps_basic.py`** - 基本的な使い方
  - dict型の依存性
  - 設定値の取得
  - 複数ツールでの依存性共有

- **`experimental_deps_advanced.py`** - 高度な使い方
  - Pydanticモデルの依存性
  - dataclassの依存性
  - 接続の再作成パターン
  - エラーハンドリング

すべてのサンプルは実際に動作確認済みです。

---

## 技術的な詳細

実装の詳細、技術的な制約、開発プロセスについては、以下を参照してください：

- [カスタムツール](custom-tools.md) - 基本的なカスタムツール機能

---

## 移行ガイド

### Phase 1から移行する場合

**Phase 1（依存性なし）**:
```python
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

model = ClaudeCodeCLIModel('claude-sonnet-4-5-20250929')
agent = Agent(model)
model.set_agent_toolsets(agent._function_toolset)

@agent.tool_plain
def my_tool(x: int) -> int:
    return x * 2
```

**Milestone 3（依存性あり）**:
```python
from pydantic_ai import RunContext
from pydantic_claude_cli import ClaudeCodeCLIModel, ClaudeCodeCLIAgent

model = ClaudeCodeCLIModel(
    'claude-sonnet-4-5-20250929',
    enable_experimental_deps=True  # 追加
)
agent = ClaudeCodeCLIAgent(model, deps_type=dict)  # 変更
model.set_agent_toolsets(agent._function_toolset)

@agent.tool  # @agent.tool_plain → @agent.tool
async def my_tool(ctx: RunContext[dict], x: int) -> int:
    config = ctx.deps.get("multiplier", 2)
    return x * config

result = await agent.run("Calculate 5 × 3", deps={"multiplier": 3})
```

### Pydantic AI標準から移行する場合

完全なRunContextサポートが必要な場合は、Pydantic AI標準の使用を推奨します：

```python
# Pydantic AI標準（完全なRunContextサポート）
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

model = AnthropicModel('claude-sonnet-4-5-20250929', api_key='...')
agent = Agent(model, deps_type=httpx.AsyncClient)

@agent.tool
async def fetch_data(ctx: RunContext[httpx.AsyncClient], url: str) -> str:
    response = await ctx.deps.get(url)  # ✅ 動作する
    ctx.retry("Retrying...")  # ✅ 動作する
    return response.text
```

---

## フィードバック

この実験的機能についてのフィードバックを歓迎します：

- [GitHub Issues](https://github.com/yourusername/pydantic-claude-cli/issues)
- ユースケースの共有
- 改善提案

フィードバックに基づいて、将来のバージョンで機能を拡張していきます。
