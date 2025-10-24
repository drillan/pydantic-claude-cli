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

**現在の選択**: ツールを完全に無効化（`allowed_tools=[]`）

**理由**:
1. 統合の複雑さ
2. MCPサーバーのセットアップが必要
3. MVP では不要

**将来の方向性**:
- MCP SDK Server を使用
- Pydantic AIのツールをMCPツールに変換
- SDK内MCPサーバーとして実行

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
