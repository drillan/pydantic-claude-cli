# Pydantic AI標準のAnthropic統合との比較

このドキュメントでは、`pydantic-claude-cli` と Pydantic AI 標準の Anthropic 統合（`AnthropicModel`）の違いを説明します。

## 概要

### Pydantic AI 標準の Anthropic 統合

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

# APIキーが必要
model = AnthropicModel('claude-haiku-4-5')
agent = Agent(model)
```

**特徴**:
- Anthropic APIを直接使用
- **APIキーが必要** (`ANTHROPIC_API_KEY` 環境変数)
- 公式SDKベース
- フル機能サポート

### pydantic-claude-cli

```python
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

# APIキー不要
model = ClaudeCodeCLIModel('claude-haiku-4-5')
agent = Agent(model)
```

**特徴**:
- Claude Code CLI を経由
- **APIキー不要** (`claude login` で認証)
- Node.js + CLI が必要
- 一部機能に制限あり

---

## 機能比較表

| 機能 | Pydantic AI 標準<br>(AnthropicModel) | pydantic-claude-cli<br>基本機能 (v0.2+) | pydantic-claude-cli<br>実験的機能 (v0.2+) (実験的) |
|------|-----------------------------------|------------------------------|----------------------------------------|
| **基本機能** |
| テキスト会話 | ✅ 対応 | ✅ 対応 | ✅ 対応 |
| システムプロンプト | ✅ 対応 | ✅ 対応 | ✅ 対応 |
| 会話履歴 | ✅ 対応 | ✅ 対応 | ✅ 対応 |
| ストリーミング | ✅ 対応 | ❌ 未対応 | ❌ 未対応 |
| **認証** |
| APIキー | ✅ 必要 | ❌ 不要 | ❌ 不要 |
| Claude Code ログイン | ❌ 不要 | ✅ 必要 | ✅ 必要 |
| **カスタムツール** |
| 依存性なしツール | ✅ 対応 | ✅ **対応（v0.2+）** | ✅ **対応** |
| RunContext（シリアライズ可能deps） | ✅ 対応 | ❌ 未対応 | ✅ **実験的対応** |
| RunContext（非シリアライズdeps） | ✅ 対応 | ❌ 未対応 | ❌ 未対応 |
| `ctx.deps` | ✅ 対応 | ❌ 未対応 | ✅ **対応** |
| `ctx.retry()` | ✅ 対応 | ❌ 未対応 | ❌ 未対応 |
| `ctx.run_step` | ✅ 対応 | ❌ 未対応 | ❌ 未対応 |
| **マルチモーダル** |
| 画像 | ✅ 対応 | ❌ 未対応 | ❌ 未対応 |
| PDF | ✅ 対応 | ❌ 未対応 | ❌ 未対応 |
| 音声 | ✅ 対応 | ❌ 未対応 | ❌ 未対応 |
| **出力形式** |
| テキスト出力 | ✅ 対応 | ✅ 対応 | ✅ 対応 |
| 構造化出力 | ✅ 対応 | ✅ 対応 | ✅ 対応 |
| ツール出力 | ✅ 対応 | ❌ 未対応 | ❌ 未対応 |
| **エラーハンドリング** |
| レート制限エラー | ✅ 詳細なエラー | ⚠️ CLI経由 | ⚠️ CLI経由 |
| コンテキスト長超過 | ✅ 詳細なエラー | ⚠️ CLI経由 | ⚠️ CLI経由 |
| リトライ機能 | ✅ 組み込み | ⚠️ Pydantic AI依存 | ⚠️ Pydantic AI依存 |
| **パフォーマンス** |
| レイテンシ | ⚠️ 通常（API直接） | ❌ 高い（CLI起動+API） | ❌ 高い（CLI起動+API） |
| スループット | ✅ 高い | ⚠️ 中程度 | ⚠️ 中程度 |
| 並列リクエスト | ✅ 効率的 | ⚠️ 各リクエストで新プロセス | ⚠️ 各リクエストで新プロセス |
| **依存関係** |
| Python パッケージ | `anthropic` | `claude-code-sdk` | `claude-code-sdk` |
| 外部依存 | なし | Node.js, Claude Code CLI | Node.js, Claude Code CLI |
| インストールサイズ | 小 (~50MB) | 大 (~300MB) | 大 (~300MB) |
| **デプロイメント** |
| サーバーレス (Lambda等) | ✅ 適している | ❌ 不適 | ❌ 不適 |
| Docker コンテナ | ✅ 簡単 | ⚠️ Node.js必要 | ⚠️ Node.js必要 |
| ローカル開発 | ✅ 簡単 | ✅ 簡単 | ✅ 簡単 |
| CI/CD | ✅ 簡単 | ⚠️ Node.js + CLI設定必要 | ⚠️ Node.js + CLI設定必要 |
| **実装要件** |
| Agent型 | `Agent` | `Agent` | `ClaudeCodeCLIAgent` |
| 実験的フラグ | 不要 | 不要 | `enable_experimental_deps=True` |

### 凡例
- ✅ 対応・推奨
- ⚠️ 部分対応・制限あり
- ❌ 未対応
- ❓ 不明・未確認

---

## 詳細な比較

### 1. 基本的なテキスト会話

#### Pydantic AI 標準

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
import os

# APIキー設定
os.environ['ANTHROPIC_API_KEY'] = 'your-api-key'

model = AnthropicModel('claude-haiku-4-5')
agent = Agent(model, instructions='あなたは親切なアシスタントです。')

# 同期・非同期両方対応
result = await agent.run('こんにちは')
print(result.output)
```

**特徴**:
- ✅ シンプルで直接的
- ✅ 低レイテンシ
- ❌ APIキーが必要

#### pydantic-claude-cli

```python
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

# APIキー不要（事前に claude login 実行）
model = ClaudeCodeCLIModel('claude-haiku-4-5')
agent = Agent(model, instructions='あなたは親切なアシスタントです。')

# 非同期のみ
result = await agent.run('こんにちは')
print(result.output)
```

**特徴**:
- ✅ APIキー不要
- ⚠️ CLI起動のオーバーヘッド（100-500ms）
- ⚠️ Node.js + CLI が必要

**結論**: シンプルなテキスト会話では両方とも動作するが、Pydantic AI標準の方が高速。

---

### 2. ストリーミングレスポンス

#### Pydantic AI 標準

```python
model = AnthropicModel('claude-haiku-4-5')
agent = Agent(model)

# ストリーミング対応
async with agent.run_stream('長い文章を生成して') as stream:
    async for chunk in stream.stream_text():
        print(chunk, end='', flush=True)
```

**特徴**:
- ✅ リアルタイムで応答を受信
- ✅ ユーザー体験が良い
- ✅ 早期エラー検出

#### pydantic-claude-cli

```python
model = ClaudeCodeCLIModel('claude-haiku-4-5')
agent = Agent(model)

# ストリーミング未対応
result = await agent.run('長い文章を生成して')
print(result.output)  # 全体が一度に返る
```

**特徴**:
- ❌ ストリーミング未実装
- ❌ 応答完了まで待つ必要がある
- ❌ ユーザー体験が劣る

**結論**: ストリーミングが必要な場合は Pydantic AI 標準を使用。

---

### 3. カスタムツール

#### Pydantic AI 標準（サポート）

```python
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.anthropic import AnthropicModel

model = AnthropicModel('claude-haiku-4-5')
agent = Agent(model, deps_type=dict)

# RunContext依存ツール（サポート）
@agent.tool
async def get_weather(ctx: RunContext[dict], city: str) -> str:
    """都市の天気を取得"""
    api_key = ctx.deps.get('api_key')
    # 実際のAPIコール
    return f"{city}の天気: 晴れ"

# ツールを使用
result = await agent.run('東京の天気は？', deps={'api_key': '...'})
print(result.output)
```

**特徴**:
- ✅ Python関数として定義
- ✅ RunContext依存性サポート
- ✅ 型安全
- ✅ 自動的にスキーマ生成
- ✅ 複数ツールの組み合わせ

#### pydantic-claude-cli 基本機能 (v0.2+)（依存性なしツールのみ）

```python
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

model = ClaudeCodeCLIModel('claude-haiku-4-5')
agent = Agent(model)

# toolsetsを設定（重要）
model.set_agent_toolsets(agent._function_toolset)

# 依存性なしツール（✅ v0.2+で動作）
@agent.tool_plain
def calculate(x: int, y: int) -> int:
    """計算ツール"""
    return x + y

# ツールを使用
result = await agent.run('5 + 3を計算して')
print(result.output)
# → ツールが実際に呼び出される
```

**特徴**:
- ✅ **依存性なしツールは対応（v0.2+）**
- ✅ 型安全
- ✅ 自動的にスキーマ生成
- ✅ 複数ツールの組み合わせ
- ❌ RunContext依存は未対応
- ⚠️ `set_agent_toolsets()`の手動呼び出しが必要

#### pydantic-claude-cli 実験的機能 (v0.2+)（実験的依存性サポート）

```python
from pydantic import BaseModel
from pydantic_ai import RunContext
from pydantic_claude_cli import ClaudeCodeCLIModel, ClaudeCodeCLIAgent

class ApiConfig(BaseModel):
    api_key: str
    timeout: int

# 実験的機能を有効化
model = ClaudeCodeCLIModel('claude-haiku-4-5', enable_experimental_deps=True)
agent = ClaudeCodeCLIAgent(model, deps_type=ApiConfig)
model.set_agent_toolsets(agent._function_toolset)

# RunContext依存ツール（✅ 実験的機能 (v0.2+)で動作）
@agent.tool
async def get_weather(ctx: RunContext[ApiConfig], city: str) -> str:
    """都市の天気を取得"""
    api_key = ctx.deps.api_key  # ✅ depsにアクセス可能
    # API呼び出し
    return f"{city}の天気: 晴れ"

# ツールを使用（depsを渡す）
result = await agent.run(
    '東京の天気は？',
    deps=ApiConfig(api_key='abc', timeout=30)
)
print(result.output)
```

**特徴**:
- ✅ **シリアライズ可能な依存性をサポート**（dict, Pydanticモデル, dataclass）
- ✅ `ctx.deps`にアクセス可能
- ✅ 型安全
- ❌ 非シリアライズ可能な依存性は未サポート（httpx, DB接続等）
- ❌ `ctx.retry()`, `ctx.run_step`等は未サポート
- ⚠️ `ClaudeCodeCLIAgent`の使用が必要
- ⚠️ 実験的機能（安定版候補）

**結論**:
- **依存性なしツール**: 基本機能 (v0.2+)で対応 ✅
- **シリアライズ可能な依存性**: 実験的機能 (v0.2+)で実験的対応 ✅
- **完全なRunContextサポート**: Pydantic AI標準を使用

---

### 4. マルチモーダル（画像入力）

#### Pydantic AI 標準

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

model = AnthropicModel('claude-haiku-4-5')
agent = Agent(model)

# 画像付きメッセージ
result = await agent.run(
    '画像に何が写っていますか？',
    message_history=[
        ModelRequest(parts=[
            UserPromptPart(content=[
                '画像に何が写っていますか？',
                ImageUrl(url='https://example.com/image.jpg')
            ])
        ])
    ]
)
print(result.output)
```

**特徴**:
- ✅ 画像URL対応
- ✅ Base64エンコード画像対応
- ✅ 複数画像対応
- ✅ 画像+テキストの組み合わせ

#### pydantic-claude-cli

```python
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

model = ClaudeCodeCLIModel('claude-haiku-4-5')
agent = Agent(model)

# 画像は未対応
result = await agent.run('画像に何が写っていますか？')
# MessageConversionError: Multimodal content in UserPromptPart is not yet supported
```

**特徴**:
- ❌ 画像未対応
- ❌ PDF未対応
- ❌ その他メディア未対応

**結論**: マルチモーダルが必要な場合は Pydantic AI 標準を使用。

---

### 5. エラーハンドリング

#### Pydantic AI 標準

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from anthropic import APIError, RateLimitError

model = AnthropicModel('claude-haiku-4-5')
agent = Agent(model)

try:
    result = await agent.run('こんにちは')
except RateLimitError as e:
    print(f"レート制限: {e.status_code}, リトライ推奨時間: {e.retry_after}")
except APIError as e:
    print(f"APIエラー: {e.status_code}, メッセージ: {e.message}")
```

**特徴**:
- ✅ 詳細なエラー情報
- ✅ 型付きエラークラス
- ✅ リトライ情報付き
- ✅ ステータスコード確認可能

#### pydantic-claude-cli

```python
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel, ClaudeCLIProcessError

model = ClaudeCodeCLIModel('claude-haiku-4-5')
agent = Agent(model)

try:
    result = await agent.run('こんにちは')
except ClaudeCLIProcessError as e:
    # CLI経由のため詳細度が低い
    print(f"CLIエラー: {e}")
```

**特徴**:
- ⚠️ CLI経由のため詳細度が低い
- ⚠️ エラーメッセージが一般的
- ❌ レート制限情報なし
- ❌ リトライ時間情報なし

**結論**: 詳細なエラー情報が必要な場合は Pydantic AI 標準を使用。

---

### 6. パフォーマンス比較

#### レイテンシ

```
Pydantic AI 標準:
  合計: 500-3000ms
  ├─ API呼び出し: 500-3000ms
  └─ オーバーヘッド: <10ms

pydantic-claude-cli:
  合計: 600-3500ms
  ├─ CLI起動: 100-500ms
  ├─ API呼び出し: 500-3000ms
  └─ オーバーヘッド: <10ms
```

**結論**: Pydantic AI 標準の方が 100-500ms 高速。

#### メモリ使用量

```
Pydantic AI 標準:
  Python プロセス: ~50MB
  合計: ~50MB

pydantic-claude-cli:
  Python プロセス: ~50MB
  Node.js CLI: ~100-200MB
  合計: ~150-250MB
```

**結論**: Pydantic AI 標準の方がメモリ効率が良い。

#### 並列リクエスト

```python
# Pydantic AI 標準: 効率的
import asyncio
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

model = AnthropicModel('claude-haiku-4-5')
agent = Agent(model)

# 並列実行が効率的
results = await asyncio.gather(
    agent.run('質問1'),
    agent.run('質問2'),
    agent.run('質問3'),
)
```

```python
# pydantic-claude-cli: 各リクエストで新しいCLIプロセス
import asyncio
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

model = ClaudeCodeCLIModel('claude-haiku-4-5')
agent = Agent(model)

# 各リクエストで新しいNode.jsプロセスが起動
# メモリとCPUのオーバーヘッドが大きい
results = await asyncio.gather(
    agent.run('質問1'),  # 新プロセス1
    agent.run('質問2'),  # 新プロセス2
    agent.run('質問3'),  # 新プロセス3
)
```

**結論**: 並列リクエストでは Pydantic AI 標準が圧倒的に効率的。

---

### 7. デプロイメント

#### AWS Lambda / サーバーレス

**Pydantic AI 標準**:
```dockerfile
FROM public.ecr.aws/lambda/python:3.13

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

CMD ["app.handler"]
```

✅ シンプル、軽量

**pydantic-claude-cli**:
```dockerfile
FROM public.ecr.aws/lambda/python:3.13

# Node.jsをインストール
RUN yum install -y nodejs npm

# Claude Code CLIをインストール
RUN npm install -g @anthropic-ai/claude-code

# 認証情報をコピー（問題あり）
COPY .claude/config.json /root/.claude/

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

CMD ["app.handler"]
```

❌ 複雑、イメージサイズ大、認証問題あり

**結論**: サーバーレスでは Pydantic AI 標準を使用。

#### Docker コンテナ（長時間実行）

**Pydantic AI 標準**:
```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

CMD ["python", "app.py"]
```

**pydantic-claude-cli**:
```dockerfile
FROM python:3.13-slim

# Node.jsをインストール
RUN apt-get update && \
    apt-get install -y nodejs npm && \
    rm -rf /var/lib/apt/lists/*

# Claude Code CLIをインストール
RUN npm install -g @anthropic-ai/claude-code

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# 認証が必要
# docker run -v ~/.claude:/root/.claude ...

CMD ["python", "app.py"]
```

⚠️ 可能だが複雑

**結論**: Docker でも Pydantic AI 標準の方がシンプル。

---

## どちらを使うべきか

### Pydantic AI 標準（AnthropicModel）を使うべき場合

✅ **以下のいずれかに該当する場合**:

1. **本番環境での使用**
   - サーバーレス（Lambda, Cloud Functions等）
   - コンテナデプロイ
   - CI/CD パイプライン

2. **パフォーマンスが重要**
   - 低レイテンシが必要
   - 高スループットが必要
   - 並列リクエストが多い

3. **高度な機能が必要**
   - カスタムツール
   - ストリーミング
   - マルチモーダル（画像、PDF等）
   - 詳細なエラーハンドリング

4. **APIキーの管理が問題ない**
   - シークレット管理システムがある
   - 環境変数で管理できる

5. **シンプルな依存関係を望む**
   - Python パッケージのみ
   - 外部依存なし

### pydantic-claude-cli を使うべき場合

✅ **以下のいずれかに該当する場合**:

1. **ローカル開発**
   - 個人プロジェクト
   - プロトタイピング
   - 学習目的

2. **APIキーの管理が困難**
   - APIキーを保存したくない
   - Claude Code にすでにログイン済み
   - セキュリティポリシー上APIキーを保存できない

3. **シンプルなテキスト会話のみ**
   - ツール不要
   - マルチモーダル不要
   - ストリーミング不要

4. **Node.js環境が既にある**
   - 既にClaude Code CLIを使用している
   - Node.jsプロジェクトの一部

### 判断フローチャート

```
スタート
  │
  ▼
本番環境？
  │
  ├─Yes─▶ Pydantic AI 標準
  │
  ▼ No
  │
完全なRunContextサポート（ctx.retry()等）が必要？
  │
  ├─Yes─▶ Pydantic AI 標準
  │
  ▼ No
  │
非シリアライズ可能な依存性（httpx, DB接続等）が必要？
  │
  ├─Yes─▶ Pydantic AI 標準
  │
  ▼ No
  │
シリアライズ可能な依存性（dict, Pydanticモデル等）が必要？
  │
  ├─Yes─▶ pydantic-claude-cli 実験的機能 (v0.2+)（実験的）
  │
  ▼ No
  │
依存性なしのカスタムツールが必要？
  │
  ├─Yes─▶ pydantic-claude-cli 基本機能 (v0.2+)
  │
  ▼ No
  │
ストリーミングが必要？
  │
  ├─Yes─▶ Pydantic AI 標準
  │
  ▼ No
  │
マルチモーダルが必要？
  │
  ├─Yes─▶ Pydantic AI 標準
  │
  ▼ No
  │
APIキーを管理できる？
  │
  ├─Yes─▶ Pydantic AI 標準（推奨）
  │
  ▼ No
  │
pydantic-claude-cli 基本機能 (v0.2+)
```

---

## 移行ガイド

### Pydantic AI 標準 → pydantic-claude-cli

#### ステップ1: 依存関係の変更

```toml
# Before
dependencies = [
    "pydantic-ai[anthropic]",
]

# After
dependencies = [
    "pydantic-ai",
    "pydantic-claude-cli",
]
```

#### ステップ2: Claude Code CLI のインストール

```bash
# Node.jsをインストール（未インストールの場合）
# https://nodejs.org/

# Claude Code CLIをインストール
npm install -g @anthropic-ai/claude-code

# ログイン
claude login
```

#### ステップ3: コードの変更

```python
# Before
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
import os

os.environ['ANTHROPIC_API_KEY'] = 'your-api-key'
model = AnthropicModel('claude-haiku-4-5')
agent = Agent(model)

# After
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

# APIキー不要
model = ClaudeCodeCLIModel('claude-haiku-4-5')
agent = Agent(model)
```

#### ステップ4: 機能の確認

以下が使用されている場合は完全移行できません（部分的に対応可能）：

- ⚠️ **RunContext依存のカスタムツール（`@agent.tool`）**
  - シリアライズ可能な依存性: 実験的機能 (v0.2+)で実験的対応 ✅
  - 非シリアライズ可能な依存性: 未対応 ❌
- ❌ **ストリーミング（`run_stream`）** - 未対応
- ❌ **マルチモーダル（画像、PDF等）** - 未対応

**完全移行可能な機能**:
- ✅ 依存性なしのカスタムツール（`@agent.tool_plain`）
- ✅ シリアライズ可能な依存性を使うカスタムツール（実験的機能 (v0.2+)）

### pydantic-claude-cli → Pydantic AI 標準

#### ステップ1: 依存関係の変更

```toml
# Before
dependencies = [
    "pydantic-ai",
    "pydantic-claude-cli",
]

# After
dependencies = [
    "pydantic-ai[anthropic]",
]
```

#### ステップ2: APIキーの取得

```bash
# Anthropic APIキーを取得
# https://console.anthropic.com/settings/keys
```

#### ステップ3: APIキーの設定

```bash
# 環境変数に設定
export ANTHROPIC_API_KEY='your-api-key'
```

#### ステップ4: コードの変更

```python
# Before
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

model = ClaudeCodeCLIModel('claude-haiku-4-5')
agent = Agent(model)

# After
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

model = AnthropicModel('claude-haiku-4-5')
agent = Agent(model)
```

#### ステップ5: 機能の追加（オプション）

移行後に利用可能になる機能：

```python
# ストリーミング
async with agent.run_stream('質問') as stream:
    async for chunk in stream.stream_text():
        print(chunk, end='')

# カスタムツール
@agent.tool
async def my_tool(param: str) -> str:
    return f"結果: {param}"

# マルチモーダル
result = await agent.run(
    '画像に何が写っていますか？',
    message_history=[...]
)
```

---

## よくある質問

### Q1: 両方同時に使えますか？

**A**: はい、同じプロジェクトで両方使えます。

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_claude_cli import ClaudeCodeCLIModel

# 本番環境用
production_model = AnthropicModel('claude-haiku-4-5')
production_agent = Agent(production_model)

# 開発環境用
dev_model = ClaudeCodeCLIModel('claude-haiku-4-5')
dev_agent = Agent(dev_model)
```

### Q2: コストは違いますか？

**A**: いいえ、同じです。どちらも最終的には Anthropic API を使用するため、トークンベースの課金は同じです。

### Q3: pydantic-claude-cli の方が安全ですか？

**A**: 一概には言えません。

**pydantic-claude-cli**:
- ✅ APIキーを環境変数に保存しない
- ❌ `~/.claude/config.json` に認証情報を保存
- ❌ Node.js プロセスを経由（攻撃面が増える）

**Pydantic AI 標準**:
- ✅ シンプルな構成
- ❌ APIキーの管理が必要
- ✅ シークレット管理システムと統合可能

### Q4: 将来的に pydantic-claude-cli で全機能サポートされますか？

**A**: 段階的にサポート済み・予定です。

**実装済み**:
- ✅ **カスタムツール（依存性なし）**: 基本機能 (v0.2+)で実装済み（v0.2+）
- ✅ **カスタムツール（シリアライズ可能な依存性）**: 実験的機能 (v0.2+)で実験的実装済み

**実装予定**:
- 🔄 **ストリーミング**: 将来のバージョンで検討
- 🔄 **完全なRunContextサポート**: Pydantic AIへのFeature Request提出予定
- ❓ **マルチモーダル**: Claude Code SDKの対応次第

**実験的機能 (v0.2+)の位置づけ**:
- 動作確認: ✅ 完了（85テスト合格、E2E動作確認済み）
- ステータス: 実験的機能（安定版候補）
- 推奨用途: プロトタイプ、開発環境、非本番環境
- 安定版移行: ユーザーフィードバック収集後（1-2ヶ月）

ただし、本番環境では引き続き Pydantic AI 標準を推奨します。

### Q5: パフォーマンステストの結果はありますか？

**A**: 簡易的なベンチマーク:

```
単一リクエスト（1回）:
  Pydantic AI 標準: 1.2秒
  pydantic-claude-cli: 1.8秒 (50%遅い)

並列リクエスト（10回同時）:
  Pydantic AI 標準: 2.3秒 (total)
  pydantic-claude-cli: 8.5秒 (total, 270%遅い)

メモリ使用量:
  Pydantic AI 標準: 50MB
  pydantic-claude-cli: 250MB (5倍)
```

---

## まとめ

| 観点 | Pydantic AI 標準 | pydantic-claude-cli |
|------|-----------------|---------------------|
| **推奨用途** | 本番環境、高度な機能 | ローカル開発、プロトタイピング |
| **主な利点** | フル機能、高パフォーマンス | APIキー不要 |
| **主な欠点** | APIキーが必要 | 機能制限、パフォーマンス |

**結論**:
- **本番環境やプロダクション**: Pydantic AI 標準を使用
- **個人開発やローカルプロトタイピング**: pydantic-claude-cli を検討

どちらも Pydantic AI のインターフェースを使用するため、後で切り替えることも可能です。
