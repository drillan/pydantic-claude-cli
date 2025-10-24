# アーキテクチャ設計書

## システム構成図

```
┌─────────────────────────────────────────────────────────────┐
│                    ユーザーアプリケーション                      │
│                                                                │
│  from pydantic_ai import Agent                                │
│  from pydantic_claude_cli import ClaudeCodeCLIModel           │
│                                                                │
│  model = ClaudeCodeCLIModel('claude-sonnet-4-5-20250929')     │
│  agent = Agent(model)                                          │
│  result = await agent.run('Hello')                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Pydantic AI Protocol
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Pydantic AI Framework                        │
│                                                                │
│  - Agent: 会話管理、ツール実行                                │
│  - ModelMessage: メッセージ抽象化                             │
│  - Model (abstract): モデルインターフェース                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Model.request(messages)
                         │
┌────────────────────────▼────────────────────────────────────┐
│              pydantic-claude-cli パッケージ                   │
│                                                                │
│  ┌──────────────────────────────────────────────────┐       │
│  │ ClaudeCodeCLIModel (Model を実装)                │       │
│  │                                                    │       │
│  │  - request(): メイン処理ロジック                  │       │
│  │  - system: プロバイダー名を返す                   │       │
│  └──────────────────────────────────────────────────┘       │
│                         │                                      │
│                         │ 使用                                 │
│                         ▼                                      │
│  ┌──────────────────────────────────────────────────┐       │
│  │ message_converter                                 │       │
│  │                                                    │       │
│  │  - convert_to_claude_prompt()                     │       │
│  │  - convert_from_claude_message()                  │       │
│  │  - extract_system_prompt()                        │       │
│  │  - extract_usage_from_result()                    │       │
│  └──────────────────────────────────────────────────┘       │
│                         │                                      │
│  ┌──────────────────────────────────────────────────┐       │
│  │ ClaudeCodeCLIProvider (Provider を実装)           │       │
│  │                                                    │       │
│  │  - _find_cli(): CLI検出                           │       │
│  │  - model_profile(): モデルプロファイル           │       │
│  └──────────────────────────────────────────────────┘       │
│                         │                                      │
│  ┌──────────────────────────────────────────────────┐       │
│  │ tool_support (v0.2+)                              │       │
│  │                                                    │       │
│  │  - requires_run_context(): 依存性検出             │       │
│  │  - find_tool_function(): 関数探索                 │       │
│  │  - extract_tools_from_agent(): ツール抽出         │       │
│  └──────────────────────────────────────────────────┘       │
│                         │                                      │
│  ┌──────────────────────────────────────────────────┐       │
│  │ tool_converter (v0.2+)                            │       │
│  │                                                    │       │
│  │  - extract_python_types(): 型変換                 │       │
│  │  - format_tool_result(): MCP形式変換              │       │
│  │  - create_mcp_from_tools(): MCPサーバー作成       │       │
│  └──────────────────────────────────────────────────┘       │
│                         │                                      │
│  ┌──────────────────────────────────────────────────┐       │
│  │ exceptions                                        │       │
│  │                                                    │       │
│  │  - ClaudeCLINotFoundError                         │       │
│  │  - ClaudeCLIProcessError                          │       │
│  │  - MessageConversionError                         │       │
│  └──────────────────────────────────────────────────┘       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ query(prompt, options)
                         │ + mcp_servers (v0.2+)
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  claude-code-sdk パッケージ                   │
│                                                                │
│  ┌──────────────────────────────────────────────────┐       │
│  │ query() 関数                                      │       │
│  │                                                    │       │
│  │  - プロンプトを受け取る                            │       │
│  │  - Transportを作成                                │       │
│  │  - メッセージをyield                              │       │
│  └──────────────────────────────────────────────────┘       │
│                         │                                      │
│  ┌──────────────────────────────────────────────────┐       │
│  │ SubprocessCLITransport                            │       │
│  │                                                    │       │
│  │  - _build_command(): CLI コマンド構築             │       │
│  │  - connect(): プロセス起動                        │       │
│  │  - write(): stdin に書き込み                      │       │
│  │  - read_messages(): stdout から読み取り          │       │
│  └──────────────────────────────────────────────────┘       │
│                         │                                      │
│  ┌──────────────────────────────────────────────────┐       │
│  │ Message Types                                     │       │
│  │                                                    │       │
│  │  - AssistantMessage                               │       │
│  │  - ResultMessage                                  │       │
│  │  - SystemMessage                                  │       │
│  └──────────────────────────────────────────────────┘       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ JSON over stdin/stdout
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Claude Code CLI (Node.js プロセス)              │
│                                                                │
│  - 認証情報の読み込み (~/.claude/config.json)                 │
│  - Anthropic API へのリクエスト                               │
│  - ストリーミング応答の処理                                    │
│  - JSON形式での出力                                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTPS
                         │
┌────────────────────────▼────────────────────────────────────┐
│                     Anthropic API                             │
│                                                                │
│  - Claude モデル (Sonnet, Haiku, Opus)                        │
│  - 認証とレート制限                                            │
│  - ストリーミングレスポンス                                     │
└─────────────────────────────────────────────────────────────┘
```

## クラス図

```
┌─────────────────────────────────────┐
│           Model (ABC)               │
│         (Pydantic AI)               │
├─────────────────────────────────────┤
│ + request()                         │
│ + request_stream()                  │
│ + system: str                       │
└───────────────┬─────────────────────┘
                │
                │ 継承
                │
┌───────────────▼─────────────────────┐
│     ClaudeCodeCLIModel              │
├─────────────────────────────────────┤
│ - _model_name: str                  │
│ - _provider: ClaudeCodeCLIProvider  │
│ - _cli_path: str | Path | None      │
│ - _max_turns: int | None            │
│ - _permission_mode: str | None      │
├─────────────────────────────────────┤
│ + __init__(model_name, ...)         │
│ + request(messages, ...) → Response │
│ + system: str                       │
└───────────────┬─────────────────────┘
                │
                │ 使用
                │
┌───────────────▼─────────────────────┐
│   ClaudeCodeCLIProvider             │
├─────────────────────────────────────┤
│ - _cli_path: str                    │
├─────────────────────────────────────┤
│ + __init__(cli_path?)               │
│ + _find_cli() → str                 │
│ + name: str                         │
│ + base_url: str                     │
│ + client: None                      │
│ + model_profile(name) → Profile?    │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│      message_converter              │
├─────────────────────────────────────┤
│ 関数群:                             │
│                                     │
│ + convert_to_claude_prompt()        │
│   : list[ModelMessage] → str        │
│                                     │
│ + extract_system_prompt()           │
│   : list[ModelMessage] → str?       │
│                                     │
│ + convert_from_claude_message()     │
│   : AssistantMessage → ModelResponse│
│                                     │
│ + extract_usage_from_result()       │
│   : dict → RequestUsage             │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│      tool_support (v0.2+)           │
├─────────────────────────────────────┤
│ 関数群:                             │
│                                     │
│ + requires_run_context()            │
│   : Callable → bool                 │
│                                     │
│ + find_tool_function()              │
│   : ToolDefinition → Callable?      │
│                                     │
│ + extract_tools_from_agent()        │
│   : Parameters → (tools, bool)      │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│      tool_converter (v0.2+)         │
├─────────────────────────────────────┤
│ 関数群:                             │
│                                     │
│ + extract_python_types()            │
│   : JSONSchema → dict[str, type]    │
│                                     │
│ + format_tool_result()              │
│   : Any → MCPToolResult             │
│                                     │
│ + create_mcp_from_tools()           │
│   : list[(ToolDef, func)]           │
│   → McpSdkServerConfig              │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         例外階層                     │
├─────────────────────────────────────┤
│ PydanticClaudeCLIError              │
│   ├── ClaudeCLINotFoundError        │
│   ├── ClaudeCLIProcessError         │
│   ├── MessageConversionError        │
│   └── ToolIntegrationError          │
└─────────────────────────────────────┘
```

## データフロー図

### リクエストフロー

```
User Code
    │
    │ await agent.run("Hello")
    ▼
Pydantic AI Agent
    │
    │ model.request(messages, settings, parameters)
    ▼
ClaudeCodeCLIModel.request()
    │
    ├─▶ メッセージ変換
    │   │
    │   ├─▶ convert_to_claude_prompt(messages)
    │   │       │
    │   │       └─▶ "Hello" (str)
    │   │
    │   └─▶ extract_system_prompt(messages)
    │           │
    │           └─▶ "あなたは親切なアシスタントです。" (str)
    │
    ├─▶ ClaudeCodeOptions 作成
    │       │
    │       └─▶ options = {
    │               model: "claude-sonnet-4-5-20250929",
    │               system_prompt: "...",
    │               max_turns: None,
    │               permission_mode: None,
    │               allowed_tools: []
    │           }
    │
    └─▶ claude_query(prompt, options)
            │
            ▼
Claude Code SDK
    │
    ├─▶ SubprocessCLITransport 作成
    │
    ├─▶ CLI コマンド構築
    │       │
    │       └─▶ ["claude", "--output-format", "stream-json",
    │            "--model", "claude-sonnet-4-5-20250929",
    │            "--input-format", "stream-json"]
    │
    ├─▶ サブプロセス起動
    │       │
    │       └─▶ Process(cmd, stdin=PIPE, stdout=PIPE)
    │
    ├─▶ stdin にプロンプト書き込み
    │       │
    │       └─▶ {"type": "user", "message": {...}}
    │
    └─▶ stdout から読み取り
            │
            └─▶ Stream of JSON messages
                    │
                    ├─▶ AssistantMessage(content=[...])
                    └─▶ ResultMessage(usage={...})
```

### レスポンスフロー

```
Claude API Response
    │
    │ Streaming JSON
    ▼
Claude Code CLI (stdout)
    │
    │ Line-delimited JSON
    ▼
SubprocessCLITransport.read_messages()
    │
    │ parse_message(line)
    ▼
Claude Code SDK (yield messages)
    │
    │ AssistantMessage, ResultMessage, etc.
    ▼
ClaudeCodeCLIModel.request()
    │
    ├─▶ メッセージ収集
    │       │
    │       └─▶ response_messages: list[Message]
    │
    ├─▶ AssistantMessage 抽出
    │       │
    │       └─▶ assistant_messages: list[AssistantMessage]
    │
    ├─▶ ResultMessage 抽出
    │       │
    │       └─▶ result_message: ResultMessage
    │
    ├─▶ メッセージ変換
    │       │
    │       └─▶ convert_from_claude_message(assistant_message)
    │               │
    │               └─▶ ModelResponse(parts=[TextPart(...)])
    │
    └─▶ 使用量情報付加
            │
            └─▶ extract_usage_from_result(result_message)
                    │
                    └─▶ ModelResponse(
                            parts=[...],
                            usage=RequestUsage(...)
                        )
```

## シーケンス図

```
User    Agent   Model   MsgConv  SDK    CLI     API
 │       │       │       │        │      │       │
 │run()  │       │       │        │      │       │
 ├──────>│       │       │        │      │       │
 │       │req()  │       │        │      │       │
 │       ├──────>│       │        │      │       │
 │       │       │conv() │        │      │       │
 │       │       ├──────>│        │      │       │
 │       │       │<──────┤        │      │       │
 │       │       │       │        │      │       │
 │       │       │query()│        │      │       │
 │       │       ├───────┼───────>│      │       │
 │       │       │       │        │spawn │       │
 │       │       │       │        ├─────>│       │
 │       │       │       │        │      │auth() │
 │       │       │       │        │      ├──────>│
 │       │       │       │        │      │<──────┤
 │       │       │       │        │<─────┤       │
 │       │       │       │        │      │       │
 │       │       │       │        │write │       │
 │       │       │       │        ├─────>│       │
 │       │       │       │        │      │req()  │
 │       │       │       │        │      ├──────>│
 │       │       │       │        │      │<──────┤
 │       │       │       │        │<─────┤ stream│
 │       │       │       │        │ msgs │       │
 │       │       │       │        │      │<──────┤
 │       │       │       │        │<─────┤ stream│
 │       │       │       │        │ done │       │
 │       │       │       │        │      │       │
 │       │       │conv() │        │      │       │
 │       │       ├──────>│        │      │       │
 │       │       │<──────┤        │      │       │
 │       │<──────┤       │        │      │       │
 │<──────┤       │       │        │      │       │
 │       │       │       │        │      │       │
```

## モジュール依存関係

```
┌──────────────────────────────────────────┐
│         ユーザーアプリケーション            │
└───────────────┬──────────────────────────┘
                │
                │ import
                ▼
┌──────────────────────────────────────────┐
│      pydantic_claude_cli/__init__.py     │
│                                           │
│  - ClaudeCodeCLIModel                     │
│  - ClaudeCodeCLIProvider                  │
│  - Exceptions                             │
└───────────────┬──────────────────────────┘
                │
    ┌───────────┼───────────┬───────────┐
    │           │           │           │
    ▼           ▼           ▼           ▼
┌───────┐  ┌────────┐  ┌────────┐  ┌───────────┐
│model  │  │provider│  │message │  │exceptions │
│.py    │  │.py     │  │converter│  │.py        │
│       │  │        │  │.py      │  │           │
└───┬───┘  └───┬────┘  └────────┘  └───────────┘
    │          │
    │          │
    │          └──────┐
    │                 │
    ▼                 ▼
┌─────────────────────────────────┐
│     外部依存                     │
│                                  │
│  - pydantic-ai                   │
│  - claude-code-sdk               │
│  - anyio                         │
└─────────────────────────────────┘
```

## 状態遷移図

### ClaudeCodeCLIModel のライフサイクル

```
       ┌──────────┐
       │  作成     │
       │(__init__)│
       └────┬─────┘
            │
            │ CLI検証
            │
            ▼
       ┌──────────┐
       │  準備完了 │
       └────┬─────┘
            │
            │ request()呼び出し
            │
            ▼
       ┌──────────┐
       │ 実行中    │
       │          │◄────┐
       │ - 変換    │     │ エラー
       │ - CLI起動 │     │ (リトライ)
       │ - 応答待機│     │
       └────┬─────┘     │
            │           │
            │ 成功      │
            ▼           │
       ┌──────────┐     │
       │ 完了      ├─────┘
       └────┬─────┘
            │
            │ 次のrequest()
            │
            └───────────┐
                        │
                        ▼
                   (準備完了へ)
```

### CLI プロセスの状態

```
     ┌─────────┐
     │ 未起動   │
     └────┬────┘
          │
          │ spawn
          ▼
     ┌─────────┐
     │ 起動中   │
     └────┬────┘
          │
          │ 認証完了
          ▼
     ┌─────────┐
     │ 準備完了 │
     └────┬────┘
          │
          │ プロンプト受信
          ▼
     ┌─────────┐
     │ 処理中   │
     └────┬────┘
          │
          │ 応答完了
          ▼
     ┌─────────┐
     │ 終了     │
     └─────────┘
```

---

## カスタムツールアーキテクチャ（v0.2+）

### コンポーネント連携図

```
┌─────────────────────────────────────────┐
│  Pydantic AI Agent                      │
│                                         │
│  @agent.tool_plain                      │
│  def my_tool(x: int, y: int) -> int:    │
│      return x + y                       │
└──────────────┬──────────────────────────┘
               │
               │ ToolDefinition
               │ (スキーマのみ)
               ▼
┌──────────────────────────────────────────┐
│  ClaudeCodeCLIModel.request()            │
│                                          │
│  1. function_toolsを検出                 │
└──────────────┬───────────────────────────┘
               │
               │ ModelRequestParameters
               ▼
┌──────────────────────────────────────────┐
│  tool_support.extract_tools_from_agent() │
│                                          │
│  1. FunctionToolsetから関数を探索         │
│  2. requires_run_context()で依存性検出   │
└──────────────┬───────────────────────────┘
               │
               │ (ToolDefinition, func)
               │ + has_context_tools: bool
               ▼
┌──────────────────────────────────────────┐
│  tool_converter.create_mcp_from_tools()  │
│                                          │
│  1. extract_python_types()で型抽出       │
│  2. @sdk_tool でMCPツール作成            │
│  3. 同期関数をasyncでラップ              │
└──────────────┬───────────────────────────┘
               │
               │ McpSdkServerConfig
               ▼
┌──────────────────────────────────────────┐
│  ClaudeCodeOptions                       │
│  mcp_servers={"custom": server}          │
└──────────────┬───────────────────────────┘
               │
               │ query(prompt, options)
               ▼
┌──────────────────────────────────────────┐
│  Claude Code CLI Process                 │
│  + In-process MCP Server                 │
│                                          │
│  1. LLMがツール呼び出しを返す            │
│  2. MCPサーバーにツール呼び出し          │
│  3. Python関数を実行                     │
│  4. 結果をLLMに返す                      │
└──────────────────────────────────────────┘
```

### カスタムツールデータフロー

```{mermaid}
sequenceDiagram
    participant User as ユーザーコード
    participant Agent as Pydantic AI Agent
    participant Model as ClaudeCodeCLIModel
    participant ToolSupport as tool_support
    participant ToolConverter as tool_converter
    participant SDK as claude-code-sdk
    participant CLI as Claude CLI
    participant MCP as In-process MCP
    participant LLM as Claude API

    User->>Agent: agent.run("Calculate 5+3")
    Agent->>Model: request(messages, parameters)

    Note over Model: カスタムツール検出
    Model->>ToolSupport: extract_tools_from_agent()
    ToolSupport->>ToolSupport: requires_run_context()
    ToolSupport-->>Model: (tools, has_context=False)

    Model->>ToolConverter: create_mcp_from_tools()
    ToolConverter->>ToolConverter: extract_python_types()
    ToolConverter->>ToolConverter: @sdk_tool でラップ
    ToolConverter-->>Model: McpSdkServerConfig

    Model->>SDK: query(prompt, options)
    Note over SDK: mcp_servers設定
    SDK->>CLI: spawn subprocess
    CLI->>MCP: MCPサーバー初期化

    CLI->>LLM: リクエスト + tools定義
    LLM-->>CLI: tool_use(name="add", args={x:5, y:3})

    CLI->>MCP: call_tool("add", {x:5, y:3})
    MCP->>MCP: Python関数実行
    MCP-->>CLI: {"content": [{"type": "text", "text": "8"}]}

    CLI->>LLM: tool_result + 結果
    LLM-->>CLI: "The answer is 8"

    CLI-->>SDK: AssistantMessage
    SDK-->>Model: AssistantMessage
    Model-->>Agent: ModelResponse
    Agent-->>User: result.data = "8"
```

### Phase 1の制約事項

**サポート対象**:
- 依存性なしツール（`@agent.tool_plain`）
- 基本型の引数（str, int, float, bool, list, dict）
- Pydanticモデルの引数
- 同期・非同期ツール

**非サポート**:
- RunContext依存ツール（`@agent.tool`）
- 依存性注入（`ctx.deps`へのアクセス）
- ModelRetryの伝播
- ツール実行のリトライ制御
```
