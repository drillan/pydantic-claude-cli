# カスタムツール機能

pydantic-claude-cliでのカスタムツールの使い方を説明します。

```{contents}
:depth: 2
:local:
```


カスタムツールは、LLMが特定のタスクを実行するために呼び出せる**ユーザー定義の関数**です。

pydantic-claude-cli v0.2+では、依存性なしツール（`@agent.tool_plain`）が**完全に動作します**。

---

## サポートされる機能（v0.2+）

**基本的なツール**:

```python
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

model = ClaudeCodeCLIModel('claude-sonnet-4-5-20250929')
agent = Agent(model)

# 重要: toolsetsを設定（必須）
model.set_agent_toolsets(agent._function_toolset)

@agent.tool_plain
def calculate(x: int, y: int) -> int:
    """計算ツール"""
    return x + y

result = await agent.run('5 + 3を計算して')
# LLMが自動的にcalculateツールを使用
```

**Pydanticモデルを使ったツール**:

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float

@agent.tool_plain
def get_total(items: list[Item]) -> float:
    """合計金額を計算"""
    return sum(item.price for item in items)

result = await agent.run('3つの商品の合計を計算')
# LLMがItemリストを生成してツールを呼び出す
```

**非同期ツール**:

```python
@agent.tool_plain
async def async_process(data: str) -> str:
    """非同期処理"""
    import asyncio
    await asyncio.sleep(0.1)
    return data.upper()
```

#### 制限事項（Phase 1）

**RunContext依存ツールは未サポート**:

```python
from pydantic_ai.tools import RunContext

# ❌ このようなツールはエラーになります
@agent.tool
async def query_db(ctx: RunContext[Database], user_id: int) -> str:
    # ctx.depsにアクセスできないため動作しません
    return await ctx.deps.query(user_id)
```

エラーメッセージ：
```
MessageConversionError: Tools that require RunContext are not supported with ClaudeCodeCLIModel.
Only context-free tools can be used.

Workaround: Use Pydantic AI standard (AnthropicModel) for context-dependent tools.
```

#### 実装の仕組み

Phase 1の実装は、Claude Code SDKの**In-process MCP Server**機能を活用しています：

```python
# 内部処理（自動）
from claude_code_sdk import create_sdk_mcp_server, tool

# Pydantic AIツールをMCPツールに変換
@tool("calculate", "計算ツール", {"x": int, "y": int})
async def wrapped(args):
    result = calculate(args["x"], args["y"])
    return {"content": [{"type": "text", "text": str(result)}]}

# MCPサーバーを作成
server = create_sdk_mcp_server("pydantic-custom-tools", tools=[wrapped])

# ClaudeCodeOptionsに設定
options = ClaudeCodeOptions(mcp_servers={"custom": server})
```

詳細は [動作の仕組み](how-it-works.md) の「カスタムツールの動作原理」セクションを参照してください。

---

## なぜpydantic-claude-cliで当初未対応だったのか

### 根本的な問題：2つの異なるツールシステム

#### Pydantic AI のツールシステム

```
┌─────────────────────────────────────┐
│      Pydantic AI Agent              │
│                                     │
│  - Python関数として定義             │
│  - @agent.tool デコレータ          │
│  - 自動スキーマ生成                 │
│  - 同一プロセス内で実行             │
│                                     │
│  Tool Registry:                     │
│  {                                  │
│    "get_weather": <function>,       │
│    "search_db": <function>,         │
│  }                                  │
└──────────┬──────────────────────────┘
           │
           │ tools=[...] を API に送信
           ▼
    ┌──────────────┐
    │ Anthropic API │
    └──────────────┘
```

#### Claude Code CLI のツールシステム

```
┌─────────────────────────────────────┐
│      Claude Code CLI                │
│                                     │
│  組み込みツール:                     │
│  - Bash: シェルコマンド実行         │
│  - Read: ファイル読み取り           │
│  - Write: ファイル書き込み          │
│  - Edit: ファイル編集               │
│  - Glob: ファイル検索               │
│  - Grep: コンテンツ検索             │
│  - WebFetch: Web取得                │
│  - Task: サブエージェント起動       │
│                                     │
│  + MCP (Model Context Protocol):    │
│    外部MCPサーバー経由のツール       │
└──────────┬──────────────────────────┘
           │
           │ CLI側で実行
           ▼
    ┌──────────────┐
    │ Anthropic API │
    └──────────────┘
```

### 問題点の詳細

#### 問題1: ツールの実行場所が異なる

**Pydantic AI 標準**:
```
ユーザーのPythonプロセス内でツールを実行
→ 直接Python関数を呼び出せる
→ データベース、API、ファイルに直接アクセス可能
```

**Claude Code CLI**:
```
CLIプロセス内でツールを実行
→ Python関数を呼び出せない
→ サブプロセス経由またはMCP経由でしかアクセスできない
```

#### 問題2: ツール定義の送信方法が異なる

**Pydantic AI 標準**:
```python
# リクエストボディに含める
POST /v1/messages
{
  "tools": [
    {"name": "get_weather", "input_schema": {...}}
  ]
}
```

**Claude Code CLI**:
```bash
# CLI引数で指定（組み込みツールのみ）
claude --allowed-tools "Bash,Read,Write"

# または MCP設定ファイル
claude --mcp-config config.json
```

#### 問題3: スキーマの伝達

**Pydantic AI 標準**:
```python
@agent.tool
def my_tool(param: str) -> str:
    ...

# 自動的にスキーマ生成 → API送信
```

**Claude Code CLI**:
```python
@agent.tool
def my_tool(param: str) -> str:
    ...

# スキーマ生成できても...
# → CLIにどうやって渡す？❌
# → CLIコマンドライン引数に含められない
```

---

## 技術的な障壁

### 障壁1: プロセス境界

```
┌──────────────────────────────┐
│   ユーザーのPythonプロセス    │
│                              │
│  @agent.tool                 │
│  def my_tool():              │
│      # データベースアクセス   │
│      return db.query(...)    │
│                              │
└──────────────────────────────┘
         ↕ プロセス境界 ❌
┌──────────────────────────────┐
│   Claude Code CLI (Node.js)  │
│                              │
│  ツールを呼び出したい...      │
│  でもPython関数にアクセス     │
│  できない！                  │
└──────────────────────────────┘
```

**問題**: Node.js プロセスから Python 関数を直接呼び出すことはできない

### 障壁2: メッセージフローの制御

Pydantic AI のツール実行フロー：

```python
# Pydantic AI Agent内部
while True:
    # 1. LLMにリクエスト
    response = await model.request(messages)

    # 2. ツール呼び出しをチェック
    if has_tool_calls(response):
        # 3. Python関数を実行
        for tool_call in response.tool_calls:
            result = await execute_tool(tool_call.name, tool_call.args)
            messages.append(tool_result(result))
        # 4. 結果を添えて再度LLMにリクエスト
        continue
    else:
        # 5. テキスト応答で終了
        return response
```

**pydantic-claude-cli の現状**:

```python
# 単一のリクエスト/レスポンス
response = await claude_query(prompt=prompt, options=options)
# → ツールループを制御できない ❌
```

CLI がツールループを内部で処理するため、Pydantic AI 側から制御できません。

### 障壁3: ツール登録の方法

**Pydantic AI が期待する方法**:

```python
# ツール定義を ModelRequestParameters に含める
model_request_parameters = ModelRequestParameters(
    function_tools=[
        ToolDefinition(
            name="get_weather",
            description="...",
            parameters_json_schema={...}
        )
    ]
)

# これを model.request() に渡す
response = await model.request(messages, settings, model_request_parameters)
```

**Claude Code CLI が期待する方法**:

```bash
# CLI起動時に指定
claude --allowed-tools "Bash,Read,Write"

# またはMCP設定
claude --mcp-config '{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["mcp_server.py"]
    }
  }
}'
```

**不一致**: Pydantic AI のツール定義を CLI に渡す標準的な方法がない

---

## 具体例で見る問題

### Pydantic AI 標準でできること

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
import httpx

model = AnthropicModel('claude-haiku-4-5')
agent = Agent(model)

# 天気APIにアクセスするツール
@agent.tool
async def get_weather(city: str) -> dict:
    """天気APIから実際のデータを取得"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.weather.com/v1/weather",
            params={"city": city, "apikey": "..."}
        )
        return response.json()

# データベースにアクセスするツール
@agent.tool
async def save_to_db(data: str) -> str:
    """データベースに保存"""
    # データベース接続（同じプロセス内）
    await db.execute("INSERT INTO logs VALUES (?)", data)
    return "保存完了"

# ファイルを処理するツール
@agent.tool
async def process_file(filepath: str) -> str:
    """ローカルファイルを処理"""
    with open(filepath) as f:
        content = f.read()
    # 処理ロジック
    return f"処理完了: {len(content)}文字"

# すべてのツールをLLMが自動的に使用
result = await agent.run(
    '東京の天気を取得して、結果をデータベースに保存して、'
    'その後 /tmp/log.txt を処理してください'
)
```

**動作**:
1. LLM が `get_weather("東京")` を呼び出す
2. Python関数が実行され、API から天気を取得
3. 結果が LLM に返る
4. LLM が `save_to_db(...)` を呼び出す
5. データベースに保存
6. LLM が `process_file("/tmp/log.txt")` を呼び出す
7. ファイル処理
8. LLM が最終的な応答を生成

### pydantic-claude-cli で同じことを試すと

```python
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

model = ClaudeCodeCLIModel('claude-haiku-4-5')
agent = Agent(model)

@agent.tool
async def get_weather(city: str) -> dict:
    """天気APIから実際のデータを取得"""
    # この関数は定義できるが...
    ...

# エラーが発生
result = await agent.run('東京の天気を教えて')
# MessageConversionError: Custom tools are not yet supported
```

**問題**:
1. ツール定義は Pydantic AI に登録される
2. `model.request()` が呼ばれる
3. ツールが存在することを検出
4. CLI にツールを渡す方法がない
5. エラーを発生させて中断

---

## 代替案と回避策

### 代替案1: Claude Code CLI の組み込みツールを使う

Claude Code CLI には既に便利なツールが組み込まれています：

```python
from pydantic_claude_cli import ClaudeCodeCLIModel

model = ClaudeCodeCLIModel(
    'claude-haiku-4-5',
    # 組み込みツールを有効化
    # allowed_tools=['Bash', 'Read', 'Write', 'Edit']
)
agent = Agent(model)

# LLMが組み込みツールを自動的に使用
result = await agent.run(
    'カレントディレクトリのファイル一覧を取得して、'
    'README.mdの内容を読み取ってください'
)
# → LLMがBashツールとReadツールを自動的に使用
```

**ただし注意**:
- `allowed_tools` を有効化すると、ファイルシステムへのアクセス権限が必要
- `permission_mode='acceptEdits'` の設定が必要な場合がある

### 代替案2: プロンプトで指示する

カスタムツールの代わりに、プロンプトで直接指示：

```python
model = ClaudeCodeCLIModel('claude-haiku-4-5')
agent = Agent(model)

# ツールなしでも実現可能な場合
result = await agent.run(
    '東京の天気を教えてください。'
    'ただし、実際のデータではなく、'
    '一般的な10月の東京の天気を説明してください。'
)
```

**制限**: 実際の外部APIやデータベースにアクセスできない

### 代替案3: 事前処理と事後処理

ツールの代わりに、Python コードで事前/事後処理：

```python
import httpx
from pydantic_claude_cli import ClaudeCodeCLIModel

model = ClaudeCodeCLIModel('claude-haiku-4-5')
agent = Agent(model)

# 事前にデータを取得
async with httpx.AsyncClient() as client:
    weather_response = await client.get(
        "https://api.weather.com/v1/weather?city=東京"
    )
    weather_data = weather_response.json()

# データをプロンプトに含める
result = await agent.run(
    f'以下の天気データを分析してください：\n{weather_data}'
)
```

**利点**: 動作する
**欠点**: LLMが自動的にツールを選択できない

### 代替案4: Pydantic AI 標準を使う

カスタムツールが必要な場合は、素直に Pydantic AI 標準を使用：

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
import os

os.environ['ANTHROPIC_API_KEY'] = 'your-api-key'
model = AnthropicModel('claude-haiku-4-5')
agent = Agent(model)

@agent.tool
async def my_custom_tool(param: str) -> str:
    # カスタムロジック
    return result

result = await agent.run('タスクを実行')
```

**推奨**: 本番環境やカスタムツールが必要な場合はこちらを使用

---

## 将来の実装可能性

### アプローチ1: MCP (Model Context Protocol) 経由

**概念**:

```
┌──────────────────────────────┐
│  Pydantic AI Agent           │
│                              │
│  @agent.tool                 │
│  def my_tool():              │
│      return ...              │
└──────────┬───────────────────┘
           │
           │ MCPサーバーとして公開
           ▼
┌──────────────────────────────┐
│  MCP SDK Server              │
│  (Python in-process)         │
│                              │
│  - create_sdk_mcp_server()   │
│  - ツールをMCP形式で公開     │
└──────────┬───────────────────┘
           │
           │ MCP プロトコル
           ▼
┌──────────────────────────────┐
│  Claude Code CLI             │
│                              │
│  --mcp-config で接続         │
└──────────────────────────────┘
```

**実装イメージ**:

```python
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel
from claude_code_sdk import create_sdk_mcp_server, tool

# Pydantic AIツールをMCPツールに変換
@tool("get_weather", "天気を取得", {"city": str})
async def get_weather_mcp(args):
    city = args["city"]
    # 実際のロジック
    return {"content": [{"type": "text", "text": f"{city}: 晴れ"}]}

# MCPサーバーを作成
mcp_server = create_sdk_mcp_server(
    name="pydantic-tools",
    tools=[get_weather_mcp]
)

# モデルに設定
model = ClaudeCodeCLIModel(
    'claude-haiku-4-5',
    mcp_servers={"pydantic-tools": mcp_server}
)
agent = Agent(model)

# 使用
result = await agent.run('東京の天気は？')
```

**課題**:
- ❌ Pydantic AI ツールを MCP 形式に自動変換する必要がある
- ❌ 依存性注入（`RunContext`）の扱いが複雑
- ❌ ツールの戻り値形式の変換が必要

### アプローチ2: ツールプロキシサーバー

**概念**:

```python
# 1. Pydantic AIツールをHTTPサーバーとして公開
from fastapi import FastAPI

app = FastAPI()

@app.post("/tools/get_weather")
async def get_weather_endpoint(city: str):
    # ツールロジック
    return {"result": f"{city}: 晴れ"}

# 2. MCPサーバーがHTTPサーバーを呼び出す
# 3. Claude Code CLIがMCPサーバーを使用
```

**課題**:
- ❌ 複雑すぎる（HTTPサーバー + MCP + CLI）
- ❌ ローカル開発には過剰
- ❌ セキュリティとポート管理の問題

### アプローチ3: ツール呼び出しの手動処理

**概念**: CLI からのツール呼び出しを検出して、Python側で処理

```python
# 疑似コード
async for message in claude_query(prompt, options):
    if isinstance(message, ToolCallMessage):
        # ツール呼び出しを検出
        tool_name = message.tool_name
        args = message.args

        # Python関数を実行
        result = await execute_pydantic_tool(tool_name, args)

        # 結果をCLIに送り返す
        await send_tool_result(result)
```

**課題**:
- ❌ `claude_query()` はストリーミングで終了するため、途中で介入できない
- ❌ `ClaudeSDKClient` を使う必要があるが、セッション管理が複雑
- ❌ Pydantic AI のステートレスなモデルと相性が悪い

---

## 現実的な解決策

### 解決策1: ハイブリッドアプローチ（推奨）

カスタムツールが必要な処理は Pydantic AI 標準を使用：

```python
import os
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_claude_cli import ClaudeCodeCLIModel

# 環境に応じて切り替え
if os.getenv('ANTHROPIC_API_KEY'):
    # APIキーがあれば標準版（カスタムツール使用可能）
    model = AnthropicModel('claude-haiku-4-5')
else:
    # APIキーがなければCLI版（ツールなし）
    model = ClaudeCodeCLIModel('claude-haiku-4-5')

agent = Agent(model)

# ツールは条件付きで定義
if isinstance(model, AnthropicModel):
    @agent.tool
    async def custom_tool(param: str) -> str:
        return "結果"
```

### 解決策2: 処理の分離

ツールが必要な部分とそうでない部分を分離：

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_claude_cli import ClaudeCodeCLIModel
import os

# ツールが必要な処理用
os.environ['ANTHROPIC_API_KEY'] = 'your-api-key'
tool_agent = Agent(AnthropicModel('claude-haiku-4-5'))

@tool_agent.tool
async def fetch_data(query: str) -> str:
    # データ取得
    return "..."

# データ取得
data = await tool_agent.run('最新のニュースを取得')

# ツール不要な分析用（APIキー不要）
analysis_agent = Agent(
    ClaudeCodeCLIModel('claude-haiku-4-5'),
    instructions='データを分析してください'
)

# 分析
result = await analysis_agent.run(f'以下のデータを分析：\n{data}')
```

### 解決策3: Claude Code CLI の組み込みツールで代用

可能な範囲で組み込みツールを活用：

```python
from pydantic_claude_cli import ClaudeCodeCLIModel

model = ClaudeCodeCLIModel('claude-haiku-4-5')
agent = Agent(model)

# ファイル操作はReadツールで代用可能
result = await agent.run(
    '/home/user/data.json を読み取って、'
    '内容を分析してください'
)
# → LLMが自動的にReadツールを使用

# シェルコマンドはBashツールで代用可能
result = await agent.run(
    'カレントディレクトリのファイル数を教えてください'
)
# → LLMが自動的にBashツール（ls | wc -l）を使用
```

**制限**:
- データベースアクセス: ❌ 不可
- 外部API呼び出し: ⚠️ Bashで `curl` を使えば可能だが非推奨
- 複雑なPythonロジック: ❌ 不可

---

## 将来の展望

### 短期（v0.2-0.3）

**実装難易度**: 中

**アプローチ**: MCP SDK Server の基本的な統合

```python
from pydantic_claude_cli import ClaudeCodeCLIModel, convert_tool_to_mcp

model = ClaudeCodeCLIModel('claude-haiku-4-5')
agent = Agent(model)

# Pydantic AIツールを定義
@agent.tool
async def simple_tool(param: str) -> str:
    return f"結果: {param}"

# 自動的にMCPツールに変換（将来の機能）
# model.enable_custom_tools([simple_tool])
```

**課題**:
- ツールの自動変換
- 依存性注入の扱い
- エラーハンドリング

### 中期（v0.4-0.6）

**実装難易度**: 高

**アプローチ**: 完全な Pydantic AI ツールサポート

```python
# 将来のビジョン
model = ClaudeCodeCLIModel('claude-haiku-4-5')
agent = Agent(model)

@agent.tool
async def complex_tool(ctx: RunContext[Deps], param: str) -> dict:
    # 依存性注入もサポート
    db = ctx.deps.database
    result = await db.query(param)
    return result

# 完全に動作
result = await agent.run('データベースからユーザー情報を取得')
```

### 長期（v1.0+）

**パリティ達成**: Pydantic AI 標準と同等の機能

**ただし現実的な判断**:
- 複雑な統合が必要な場合は Pydantic AI 標準を使う方が合理的
- pydantic-claude-cli はシンプルなユースケースに特化

---

## まとめ

### カスタムツールが未対応の理由

1. **プロセス境界**: Python関数をNode.jsプロセスから呼べない
2. **メッセージフロー制御**: CLIがツールループを制御
3. **ツール登録方法の不一致**: 標準的な統合方法がない

### 現実的な対応

| シナリオ | 推奨アプローチ |
|---------|---------------|
| カスタムツールが必須 | → Pydantic AI 標準を使用 |
| ファイル操作のみ | → CLI組み込みツール（Read, Write等） |
| シェルコマンド実行のみ | → CLI組み込みツール（Bash） |
| 外部API呼び出し | → 事前にデータ取得してプロンプトに含める |
| データベースアクセス | → Pydantic AI 標準を使用 |

### 将来的な可能性

- ⚠️ **MCP経由での統合**: 技術的に可能だが複雑
- ⚠️ **簡易的なツールサポート**: 制限付きで可能性あり
- ❌ **完全なパリティ**: 現実的ではない

**最終的な推奨**:
- カスタムツールが必要 → Pydantic AI 標準
- APIキー不要が最優先 → pydantic-claude-cli（ツールなし）
