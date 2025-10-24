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
│  │ exceptions                                        │       │
│  │                                                    │       │
│  │  - ClaudeCLINotFoundError                         │       │
│  │  - ClaudeCLIProcessError                          │       │
│  │  - MessageConversionError                         │       │
│  └──────────────────────────────────────────────────┘       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ query(prompt, options)
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
