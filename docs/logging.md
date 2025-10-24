# ロギングとトレーシング

pydantic-claude-cliのログ機能について説明します。

```{contents}
:depth: 2
:local:
```

---

## ログレベル

pydantic-claude-cliは、標準ライブラリの`logging`を使用して、以下の情報をログ出力します：

- **DEBUG**: 詳細な内部動作（ツール抽出、MCP変換等）
- **INFO**: 重要なイベント（MCPサーバー作成、ツール呼び出し等）
- **WARNING**: 警告（ツール関数が見つからない等）
- **ERROR**: エラー（変換失敗、CLI起動失敗等）

---

## 基本的な使い方

### ログの有効化

```python
import logging

# pydantic-claude-cliのログを有効化
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 使用
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

model = ClaudeCodeCLIModel('claude-sonnet-4-5-20250929')
agent = Agent(model)

# ログが出力される
result = await agent.run('Hello')
```

### カスタムツールのログ

カスタムツール使用時は、より詳細なログが出力されます：

```python
import logging

# DEBUGレベルで詳細ログ
logging.basicConfig(level=logging.DEBUG)

model = ClaudeCodeCLIModel('claude-sonnet-4-5-20250929')
agent = Agent(model)
model.set_agent_toolsets(agent._function_toolset)

@agent.tool_plain
def my_tool(x: int) -> int:
    return x * 2

result = await agent.run('Use my_tool with x=5')

# 出力例:
# INFO - pydantic_claude_cli.tool_support - Extracted 1 tools from agent
# INFO - pydantic_claude_cli.tool_converter - Creating MCP server with 1 tools
# DEBUG - pydantic_claude_cli.model - Using ClaudeSDKClient for MCP tools
```

---

## Pydantic Logfire統合

Pydantic AIは[Pydantic Logfire](https://logfire.pydantic.dev/)をサポートしています。
pydantic-claude-cliでも、Pydantic AIのインストルメンテーション機能を利用できます。

### セットアップ

```bash
# Logfireをインストール
pip install logfire

# 認証
logfire auth

# プロジェクト作成
logfire projects new
```

### 使用方法

```python
import logfire
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

# Logfireを設定
logfire.configure()
logfire.instrument_pydantic_ai()

# Agentを作成
model = ClaudeCodeCLIModel('claude-sonnet-4-5-20250929')
agent = Agent(model)

# カスタムツール
model.set_agent_toolsets(agent._function_toolset)

@agent.tool_plain
def calculate(x: int, y: int) -> int:
    return x + y

# 実行（Logfireにトレースが送信される）
result = await agent.run('Calculate 5 + 3')
```

Logfireダッシュボードで以下が確認できます：
- Agent実行のトレース
- ツール呼び出しの詳細
- レイテンシ情報
- エラーの詳細

---

## OpenTelemetry統合

Pydantic AIはOpenTelemetryをサポートしているため、任意のOTelバックエンドにデータを送信できます。

### 例: カスタムOTelバックエンド

```python
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import set_tracer_provider

from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

# OTel設定
exporter = OTLPSpanExporter(endpoint="http://localhost:4318")
span_processor = BatchSpanProcessor(exporter)
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(span_processor)
set_tracer_provider(tracer_provider)

# Agent instrumentation
Agent.instrument_all()

# 使用
model = ClaudeCodeCLIModel('claude-sonnet-4-5-20250929')
agent = Agent(model)

result = await agent.run('Hello')
# → OTelバックエンドにトレースが送信される
```

---

## カスタムツールのトレーシング

カスタムツール実行時の詳細をログに記録できます：

### ツール内でのログ

```python
import logging

logger = logging.getLogger(__name__)

@agent.tool_plain
def complex_calculation(x: int, y: int) -> int:
    logger.info(f"Starting calculation: x={x}, y={y}")

    result = x * y + x - y

    logger.info(f"Calculation complete: result={result}")
    return result
```

### Logfireでのトレース

```python
import logfire

@agent.tool_plain
def my_tool(x: int) -> int:
    with logfire.span('Tool execution', x=x):
        result = x * 2
        logfire.info('Tool result', result=result)
        return result
```

---

## 環境変数による制御

ログレベルを環境変数で制御できます：

```bash
# DEBUGレベル
export PYDANTIC_CLAUDE_CLI_LOG_LEVEL=DEBUG
uv run python app.py

# INFOレベル（デフォルト）
export PYDANTIC_CLAUDE_CLI_LOG_LEVEL=INFO

# ログ無効化
export PYDANTIC_CLAUDE_CLI_LOG_LEVEL=WARNING
```

---

## トラブルシューティング用ログ

### カスタムツールのデバッグ

```python
import logging

# 詳細ログを有効化
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# ツール呼び出しの確認
logger = logging.getLogger('pydantic_claude_cli.tool_converter')
logger.setLevel(logging.DEBUG)
```

### MCPサーバーのデバッグ

```python
# MCP関連のログのみを表示
logging.getLogger('pydantic_claude_cli.mcp_server_fixed').setLevel(logging.DEBUG)
logging.getLogger('pydantic_claude_cli.tool_converter').setLevel(logging.DEBUG)
```

---

## ベストプラクティス

### 1. 本番環境ではINFOレベル

```python
import logging

if os.getenv('ENV') == 'production':
    logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig(level=logging.DEBUG)
```

### 2. 構造化ログの使用

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': record.created,
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        return json.dumps(log_data)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.addHandler(handler)
```

### 3. Logfireとの併用

```python
import logfire
import logging

# Logfireを設定
logfire.configure()
logfire.instrument_pydantic_ai()

# 標準ライブラリloggingも併用
logging.basicConfig(level=logging.INFO)

# 両方にログが送信される
```

---

## 参考資料

- [Pydantic Logfire](https://logfire.pydantic.dev/)
- [OpenTelemetry for Python](https://opentelemetry.io/docs/languages/python/)
- [Python logging](https://docs.python.org/ja/3/library/logging.html)
