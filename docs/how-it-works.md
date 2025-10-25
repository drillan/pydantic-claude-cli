# pydantic-claude-cli の動作の仕組み

このドキュメントでは、`pydantic-claude-cli` がどのように動作するか、その内部構造と設計について詳しく説明します。

```{contents}
:depth: 2
:local:
```

---

## 概要

### 基本的な仕組み

`pydantic-claude-cli` は、Pydantic AI と Claude Code CLI の橋渡しをするアダプターです。

```
┌─────────────────┐
│  Pydantic AI    │
│     Agent       │
└────────┬────────┘
         │
         │ ModelRequest
         │
         ▼
┌─────────────────┐
│ ClaudeCodeCLI   │
│     Model       │
└────────┬────────┘
         │
         │ メッセージ変換
         │
         ▼
┌─────────────────┐
│  Claude Code    │
│      CLI        │
│  (サブプロセス)  │
└────────┬────────┘
         │
         │ JSON over stdin/stdout
         │
         ▼
┌─────────────────┐
│   Claude API    │
│  (Anthropic)    │
└─────────────────┘
```

### なぜAPIキーが不要なのか

Claude Code CLI が認証を処理するため、APIキーは不要です：

1. ユーザーは事前に `claude login` でログイン
2. CLI がログイン情報を保存
3. CLI が自動的に認証ヘッダーを付与
4. Pydantic AI アプリはAPIキーを知る必要がない

---

## アーキテクチャ全体像

### コンポーネント構成

```
pydantic_claude_cli/
├── __init__.py              # 公開API
├── model.py                 # ClaudeCodeCLIModel (メイン)
├── provider.py              # ClaudeCodeCLIProvider
├── message_converter.py     # メッセージ変換
└── exceptions.py            # カスタム例外
```

### 依存関係

```
pydantic-claude-cli
├── pydantic-ai (必須)
│   └── Pydantic AIの抽象クラスを実装
├── claude-code-sdk (必須)
│   └── Claude Code CLIとの通信
└── anyio (必須)
    └── 非同期I/O処理
```

---

## コンポーネント詳細

### 1. ClaudeCodeCLIModel

**役割**: Pydantic AI の `Model` 抽象クラスを実装し、Claude Code CLI経由でモデルにアクセス

**主要メソッド**:

```python
class ClaudeCodeCLIModel(Model):
    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        # 1. メッセージを変換
        # 2. Claude Code CLIを起動
        # 3. 応答を収集
        # 4. ModelResponseに変換
        pass
```

**初期化パラメータ**:

- `model_name`: 使用するClaudeモデル名
- `cli_path`: CLIの場所（オプション）
- `max_turns`: 会話ターン数の上限
- `permission_mode`: 権限モード

### 2. ClaudeCodeCLIProvider

**役割**: Pydantic AI の `Provider` 抽象クラスを実装し、CLI の検出と設定を管理

**主要機能**:

```python
class ClaudeCodeCLIProvider(Provider[None]):
    def _find_cli(self, cli_path: str | Path | None) -> str:
        # 1. カスタムパスをチェック
        # 2. PATH環境変数をチェック
        # 3. 一般的なインストール場所をチェック
        # 4. 見つからなければエラー
        pass
```

**CLI検索順序**:

1. 明示的に指定されたパス
2. `which claude` (PATH内)
3. `~/.npm-global/bin/claude`
4. `/usr/local/bin/claude`
5. `~/.local/bin/claude`
6. `~/node_modules/.bin/claude`
7. `~/.yarn/bin/claude`

### 3. message_converter.py

**役割**: Pydantic AI と Claude Code SDK のメッセージ形式を相互変換

**変換関数**:

#### Pydantic AI → Claude SDK

```python
def convert_to_claude_prompt(messages: list[ModelMessage]) -> str:
    # ModelRequest/ModelResponse → 文字列プロンプト
    pass

def extract_system_prompt(messages: list[ModelMessage]) -> str | None:
    # SystemPromptPart を抽出
    pass
```

#### Claude SDK → Pydantic AI

```python
def convert_from_claude_message(
    message: AssistantMessage,
    model_name: str | None = None
) -> ModelResponse:
    # AssistantMessage → ModelResponse
    pass

def extract_usage_from_result(result_data: dict[str, Any]) -> RequestUsage:
    # ResultMessage → RequestUsage
    pass
```

### 4. exceptions.py

**役割**: 明確なエラーメッセージを提供するカスタム例外

**例外階層**:

```
PydanticClaudeCLIError (基底)
├── ClaudeCLINotFoundError
├── ClaudeCLIProcessError
├── MessageConversionError
└── ToolIntegrationError
```

---

## リクエストフロー

### 完全なリクエストフロー

```
1. ユーザーコード
   ↓
   agent.run("こんにちは")

2. Pydantic AI Agent
   ↓
   model.request(messages, settings, parameters)

3. ClaudeCodeCLIModel.request()
   ↓
   3.1 メッセージ変換
       convert_to_claude_prompt(messages)
       extract_system_prompt(messages)
   ↓
   3.2 ClaudeCodeOptions作成
       options = ClaudeCodeOptions(
           model=model_name,
           system_prompt=system_prompt,
           max_turns=max_turns,
           permission_mode=permission_mode,
           allowed_tools=[],  # 初期版では無効
       )
   ↓
   3.3 Claude Code SDK呼び出し
       async for message in claude_query(prompt=prompt, options=options):
           ...

4. Claude Code SDK (claude_code_sdk)
   ↓
   4.1 SubprocessCLITransportを作成
   ↓
   4.2 CLIコマンドを構築
       ["claude", "--output-format", "stream-json", "--model", "...", ...]
   ↓
   4.3 サブプロセスとしてCLIを起動
       await anyio.open_process(cmd, stdin=PIPE, stdout=PIPE)
   ↓
   4.4 プロンプトをstdinに書き込み
       await stdin.write(json.dumps(message) + "\n")
   ↓
   4.5 stdoutからJSON応答を読み取り
       async for line in stdout:
           data = json.loads(line)
           yield parse_message(data)

5. Claude Code CLI (Node.js)
   ↓
   5.1 認証情報を読み込み
   ↓
   5.2 Anthropic APIにリクエスト
   ↓
   5.3 ストリーミング応答をJSON形式で出力

6. レスポンス処理
   ↓
   6.1 メッセージを収集
       - UserMessage
       - AssistantMessage
       - SystemMessage
       - ResultMessage
   ↓
   6.2 AssistantMessageを変換
       convert_from_claude_message(assistant_message)
   ↓
   6.3 使用量情報を抽出
       extract_usage_from_result(result_message)

7. ModelResponseを返す
   ↓
   Pydantic AI Agentに戻る
   ↓
   ユーザーコードに結果を返す
```

### タイミング図

```
User Code          Pydantic AI        Model              CLI Process        Claude API
   |                    |                |                     |                  |
   |--agent.run()------>|                |                     |                  |
   |                    |--request()---->|                     |                  |
   |                    |                |--spawn process----->|                  |
   |                    |                |                     |--authenticate--->|
   |                    |                |                     |<----token--------|
   |                    |                |<----ready-----------|                  |
   |                    |                |--write prompt------>|                  |
   |                    |                |                     |--API request---->|
   |                    |                |                     |<----stream-------|
   |                    |                |<----messages--------|                  |
   |                    |                |                     |<----stream-------|
   |                    |                |<----messages--------|                  |
   |                    |                |                     |<----done---------|
   |                    |                |<----ResultMessage---|                  |
   |                    |<--ModelResponse|                     |                  |
   |<--AgentRunResult---|                |                     |                  |
   |                    |                |--cleanup----------->|                  |
```

---

## メッセージ変換

### Pydantic AI のメッセージ構造

```python
# ModelRequest
ModelRequest(
    parts=[
        SystemPromptPart(content="あなたは親切なアシスタントです。"),
        UserPromptPart(content="こんにちは"),
    ]
)

# ModelResponse
ModelResponse(
    parts=[
        TextPart(content="こんにちは！"),
    ],
    usage=RequestUsage(...),
    model_name="claude-sonnet-4-5-20250929",
)
```

### Claude Code SDK のメッセージ構造

```python
# AssistantMessage
AssistantMessage(
    content=[
        TextBlock(text="こんにちは！"),
    ],
    model="claude-sonnet-4-5-20250929",
)

# ResultMessage
ResultMessage(
    subtype="result",
    duration_ms=1234,
    usage={"input_tokens": 10, "output_tokens": 5},
    total_cost_usd=0.0001,
)
```

### 変換の課題と対応

#### 1. システムプロンプト

**問題**: Pydantic AI はメッセージの一部、Claude SDK は別パラメータ

**解決**:
```python
# メッセージから抽出
system_prompt = extract_system_prompt(messages)

# ClaudeCodeOptionsに設定
options = ClaudeCodeOptions(
    system_prompt=system_prompt,
    ...
)
```

#### 2. 会話履歴

**問題**: Pydantic AI はメッセージリスト、Claude SDK は単一プロンプト

**解決**:
```python
# 初期版: すべてを単一のプロンプトに結合
prompt_parts = []
for message in messages:
    if isinstance(message, ModelRequest):
        for part in message.parts:
            if isinstance(part, UserPromptPart):
                prompt_parts.append(part.content)
    elif isinstance(message, ModelResponse):
        for part in message.parts:
            if isinstance(part, TextPart):
                prompt_parts.append(f"Assistant: {part.content}")

prompt = "\n\n".join(prompt_parts)
```

#### 3. ツール呼び出し

**問題**: 両方とも異なるツールシステムを持つ

**現在の対応**: 未実装（`allowed_tools=[]`）

**将来の対応**: MCP (Model Context Protocol) 経由の統合を検討

#### 4. 使用量トラッキング

**問題**: 形式が異なる

**解決**:
```python
def extract_usage_from_result(result_data: dict) -> RequestUsage:
    usage_dict = result_data.get("usage", {})
    return RequestUsage(
        request_tokens=usage_dict.get("input_tokens", 0),
        response_tokens=usage_dict.get("output_tokens", 0),
        total_tokens=usage_dict.get("input_tokens", 0)
                    + usage_dict.get("output_tokens", 0),
        details={
            "duration_ms": result_data.get("duration_ms"),
            "total_cost_usd": result_data.get("total_cost_usd"),
        },
    )
```

---

## エラーハンドリング

### エラー検出と変換

```python
try:
    async for message in claude_query(prompt=prompt, options=options):
        ...
except Exception as e:
    # CLI未検出エラー
    if "CLI not found" in str(e):
        raise ClaudeCLINotFoundError() from e

    # プロセスエラー
    raise ClaudeCLIProcessError(f"Failed to query: {e}") from e
```

### エラーの種類

#### 1. ClaudeCLINotFoundError

**発生条件**:
- CLI が PATH に存在しない
- 指定されたパスにCLIが存在しない
- Node.js がインストールされていない

**ユーザーへのアドバイス**:
```
Claude Code CLI not found. Please install it:

1. Install Node.js from: https://nodejs.org/
2. Install Claude Code CLI:
   npm install -g @anthropic-ai/claude-code
```

#### 2. ClaudeCLIProcessError

**発生条件**:
- CLI プロセスの起動失敗
- CLI プロセスが異常終了
- stdout/stdin の通信エラー

#### 3. MessageConversionError

**発生条件**:
- 未対応のメッセージ形式
- マルチモーダルコンテンツ（画像など）
- カスタムツールの使用

#### 4. ToolIntegrationError

**発生条件**:
- カスタムツールの定義を検出
- 現在は未実装

---

## 制限事項と設計上の選択

### 1. ステートレス vs ステートフル

**Pydantic AI**: ステートレス（各リクエストが独立）

**Claude Code SDK**: ステートフル（ClaudeSDKClientが会話を管理）

**選択した解決策**:
- 各リクエストで `query()` 関数を使用（一発リクエスト）
- `ClaudeSDKClient` は使用しない

**トレードオフ**:
- ✅ シンプルな実装
- ✅ Pydantic AIの設計に適合
- ❌ 会話コンテキストの管理が複雑

### 2. ツールシステム

**問題**: 2つの異なるツールシステム

```
Pydantic AI:
  - @agent.tool デコレータ
  - Python関数として定義
  - 動的にスキーマ生成

Claude Code CLI:
  - 組み込みツール（Bash, Read, Write等）
  - CLI引数で制御
  - MCPサーバー経由のカスタムツール
```

**基本機能 (v0.2+)の実装（v0.2+）**: 依存性なしツールをサポート

```python
# カスタムツールの使用例
@agent.tool_plain
def add(x: int, y: int) -> int:
    return x + y

# MCPサーバーとして自動変換される
```

**実装方法**:
1. `tool_support.py`でツールを抽出
2. `tool_converter.py`でMCPツールに変換
3. `create_sdk_mcp_server()`でIn-process MCPサーバー作成
4. `ClaudeCodeOptions.mcp_servers`に設定

**制限事項**:
- RunContext依存ツール（`@agent.tool`）は未サポート
- 依存性注入（`ctx.deps`）にアクセス不可

### 3. ストリーミング

**現在の状態**: 未実装

**理由**:
1. メッセージ変換の複雑さ
2. Claude SDKのストリーミングイベントとPydantic AIのイベントの違い
3. MVPでは不要

**実装方針**:
```python
@asynccontextmanager
async def request_stream(
    self,
    messages: list[ModelMessage],
    model_settings: ModelSettings | None,
    model_request_parameters: ModelRequestParameters,
    run_context: RunContext[Any] | None = None,
) -> AsyncIterator[StreamedResponse]:
    # ClaudeCodeCLIStreamedResponseを実装
    # _get_event_iterator()でイベントを変換
    pass
```

### 4. マルチモーダルコンテンツ

**現在の状態**: 未実装

**理由**:
1. Claude Code SDK のサポートを確認中
2. ファイルパスの処理が複雑
3. MVPでは不要

### 5. 会話履歴の管理

**現在の実装**: すべてのメッセージを単一プロンプトに結合

**問題点**:
- 長い会話でプロンプトが巨大化
- トークン制限に達する可能性

**将来の改善**:
- 会話履歴の要約
- 古いメッセージの削除
- コンテキストウィンドウ管理

---

## パフォーマンスとリソース管理

### サブプロセス管理

各リクエストで新しいCLIプロセスを起動：

```python
# 各リクエスト
await anyio.open_process(cmd, stdin=PIPE, stdout=PIPE)
# リクエスト完了後、プロセスは自動終了
```

**トレードオフ**:
- ✅ シンプル、リークなし
- ❌ 起動オーバーヘッド（~100-500ms）

### メモリ使用量

```
User Code:           ~10 MB
Pydantic AI:         ~50 MB
pydantic-claude-cli: ~10 MB
Claude Code CLI:     ~100-200 MB (Node.js)
Total:               ~170-270 MB
```

### レイテンシ

```
合計レイテンシ = 起動 + 認証 + API + 変換

起動:   100-500ms  (CLIプロセス)
認証:   0ms        (キャッシュ済み)
API:    500-5000ms (モデルによる)
変換:   <10ms      (メッセージ変換)

合計:   600-5500ms
```

---

## カスタムツールの動作原理（v0.2+）

### 基本機能 (v0.2+): 依存性なしツールのサポート

#### 実行フロー

1. **ツール定義**:

```python
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

model = ClaudeCodeCLIModel('claude-sonnet-4-5-20250929')
agent = Agent(model)

@agent.tool_plain
def add(x: int, y: int) -> int:
    """Add two numbers"""
    return x + y
```

2. **ツール抽出と検証** (`tool_support.py`):

```python
# Agent内部でToolDefinitionが生成される
tool_def = ToolDefinition(
    name="add",
    description="Add two numbers",
    parameters_json_schema={
        "type": "object",
        "properties": {
            "x": {"type": "integer"},
            "y": {"type": "integer"}
        }
    }
)

# FunctionToolsetから実行関数を探索
func = find_tool_function(tool_def, agent_toolsets)

# RunContext依存性をチェック
has_context = requires_run_context(func)  # → False（依存性なし）
```

3. **SDK MCP変換** (`tool_converter.py`):

```python
# JSON SchemaからPython型を抽出
input_schema = extract_python_types(tool_def.parameters_json_schema)
# → {"x": int, "y": int}

# SDK MCPツールを作成
@sdk_tool("add", "Add two numbers", {"x": int, "y": int})
async def wrapped(args):
    result = await func(**args)  # 元の関数を実行
    return format_tool_result(result)  # MCP形式に変換
```

4. **MCPサーバー作成**:

```python
# In-process MCPサーバーを生成
server = create_sdk_mcp_server(
    name="pydantic-custom-tools",
    version="1.0.0",
    tools=[wrapped]
)
# → McpSdkServerConfig (TypedDict)
```

5. **CLI実行**:

```python
# ClaudeCodeOptionsに設定
options = ClaudeCodeOptions(
    model="claude-sonnet-4-5-20250929",
    mcp_servers={"custom": server}
)

# CLIプロセス内でツールを実行
async for message in claude_query(prompt, options):
    # LLMがツールを呼び出し
    # MCPサーバーがPython関数を実行
    # 結果がLLMに返される
    ...
```

#### データフロー詳細

```
User Request: "Calculate 5 + 3"
    ↓
Agent.run()
    ↓
Model.request(messages, parameters)
    ↓
[カスタムツール処理]
    ├─ extract_tools_from_agent()
    │   ├─ find_tool_function(tool_def)
    │   │   └→ add: Callable
    │   └─ requires_run_context(add)
    │       └→ False (OK)
    │
    ├─ create_mcp_from_tools()
    │   ├─ extract_python_types()
    │   │   └→ {"x": int, "y": int}
    │   ├─ @sdk_tool でラップ
    │   └─ create_sdk_mcp_server()
    │       └→ McpSdkServerConfig
    │
    └─ ClaudeCodeOptions(
            mcp_servers={"custom": server}
        )
    ↓
claude_query(prompt, options)
    ↓
[Claude CLI Process]
    ├─ LLM Request + tools定義
    ├─ LLM Response: tool_use(add, {x:5, y:3})
    ├─ MCP call_tool("add", ...)
    ├─ Python func execution: add(5, 3) → 8
    ├─ MCP result: {"content": [...]}
    ├─ LLM Request + tool_result
    └─ LLM Response: "The sum is 8"
    ↓
ModelResponse
    ↓
User: result.data = "8"
```

#### 技術的な特徴

**In-process MCP Server**:
- サブプロセスではなく、同一プロセス内で実行
- IPCオーバーヘッドがない
- デバッグが容易

**制限事項と対応状況**:

**基本機能 (v0.2+)の制限**:
- RunContext依存ツールは、CLI経由では`ctx.deps`にアクセスできない
- プロセス境界を超えて依存性を渡すことが困難

**実験的機能 (v0.2+)の解決策（実験的）**:
- ✅ ContextVarを使用して依存性を転送
- ✅ シリアライズ可能な依存性のみサポート
- ✅ `ClaudeCodeCLIAgent`でContextVarを管理
- 詳細: [実験的依存性サポート](experimental-deps.md)

---

## デバッグとトラブルシューティング

### ログ出力

Claude Code SDK は内部的にログを出力しません。デバッグには環境変数を使用：

```bash
# 詳細ログを有効化
export CLAUDE_SDK_DEBUG=1

# 実行
uv run python examples/basic_usage.py
```

### よくある問題

#### 1. "CLI not found"

**確認事項**:
```bash
# CLIが存在するか
which claude

# Node.jsが存在するか
which node

# CLIのバージョン
claude --version
```

#### 2. "Not logged in"

**解決方法**:
```bash
claude login
```

#### 3. "Permission denied"

**解決方法**:
```python
model = ClaudeCodeCLIModel(
    'claude-sonnet-4-5-20250929',
    permission_mode='acceptEdits'
)
```

#### 4. 空の応答

**原因**: メッセージ変換エラーの可能性

**デバッグ**:
```python
# 変換前のメッセージを確認
print(messages)

# 変換後のプロンプトを確認
prompt = convert_to_claude_prompt(messages)
print(prompt)
```

---

## まとめ

`pydantic-claude-cli` の設計の核心：

1. **シンプルさ優先**: MVPとして最小限の機能で動作
2. **ステートレス**: Pydantic AIの設計に適合
3. **プロセス分離**: 各リクエストで独立したCLIプロセス
4. **段階的実装**: まずテキストのみ、将来的に拡張

この設計により、APIキー不要でClaudeモデルを使用できる、シンプルで信頼性の高い実装を実現しています。
