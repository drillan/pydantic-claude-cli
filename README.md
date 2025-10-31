# pydantic-claude-cli

Pydantic AI用のClaude Code CLIアダプター

このパッケージを使用すると、[Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)を介して[Pydantic AI](https://ai.pydantic.dev/)でClaudeモデルを使用できます。

## 特徴

- ✅ **簡単統合** - Pydantic AIモデルのドロップイン置き換え
- ✅ **テキストベース会話** - テキストチャットをサポート
- ✅ **カスタムツール** - 依存性なしツールをサポート
- ✅ **実験的依存性サポート** - シリアライズ可能な依存性をサポート（実験的機能）
- ⚠️ **マルチモーダル** - 画像/ファイル未対応

## 必要要件

1. **Node.js** - Claude Code CLIに必要
2. **Claude Code CLI** - インストールと認証が必要
3. **Python 3.13+** - Pydantic AI実行用

## インストール

### 1. Claude Code CLIのインストール

```bash
# Node.jsがインストールされていない場合は https://nodejs.org/ からインストール

# Claude Code CLIをグローバルインストール
npm install -g @anthropic-ai/claude-code

# Claude Codeにログイン（プロンプトに従う）
claude login
```

### 2. pydantic-claude-cliのインストール

```bash
# uv使用（推奨）
uv add git+https://github.com/drillan/pydantic-claude-cli

# またはpip使用
pip install git+https://github.com/drillan/pydantic-claude-cli
```

## クイックスタート

```python
import asyncio
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

async def main():
    # モデルインスタンス作成 - APIキー不要
    model = ClaudeCodeCLIModel('claude-haiku-4-5')

    # Pydantic AI Agentで使用
    agent = Agent(
        model,
        instructions='あなたは親切なアシスタントです。'
    )

    # クエリ実行
    result = agent.run_sync('こんにちは、Claude')
    print(result.output)

if __name__ == '__main__':
    asyncio.run(main())
```

## 使用例

### 基本的な会話

```python
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

model = ClaudeCodeCLIModel('claude-haiku-4-5')
agent = Agent(model, instructions='簡潔で親切に答えてください。')

result = agent.run_sync('量子コンピューティングを一文で説明してください。')
print(result.output)
```

### カスタム設定

```python
from pydantic_claude_cli import ClaudeCodeCLIModel

model = ClaudeCodeCLIModel(
    'claude-haiku-4-5',
    max_turns=10,  # 会話ターン数を制限
    permission_mode='acceptEdits',  # 編集を自動承認
    cli_path='/custom/path/to/claude',  # カスタムCLIパス
)
```

### カスタムツールの使用

依存性なしツール（`@agent.tool_plain`）が動作します：

```python
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

model = ClaudeCodeCLIModel('claude-haiku-4-5')
agent = Agent(model)

# 重要: Agent作成後にtoolsetsを設定
model.set_agent_toolsets(agent._function_toolset)

# カスタムツールを定義
@agent.tool_plain
def calculate_total(prices: list[float]) -> float:
    """価格リストの合計を計算"""
    return sum(prices)

@agent.tool_plain
def format_currency(amount: float, currency: str = "JPY") -> str:
    """金額を通貨形式でフォーマット"""
    return f"{amount:,.0f} {currency}"

# 実行
result = agent.run_sync('100円、200円、300円の合計を通貨形式で表示して')
print(result.output)
```

**重要**: `model.set_agent_toolsets(agent._function_toolset)` の呼び出しが必要です。

**サポート機能**:
- ✅ 基本型のツール（int, str, float, bool, list, dict）
- ✅ Pydanticモデルを引数に取るツール
- ✅ 同期・非同期ツール
- ✅ 複数ツールの連携
- ✅ 実際のツール呼び出し確認済み

**実験的機能**:
- ✅ 依存性注入（RunContext + deps）のサポート
- ✅ シリアライズ可能な依存性（dict, Pydanticモデル、dataclass）
- ⚠️ 非シリアライズ可能な依存性（httpx, DB接続等）は未サポート
- ⚠️ EmulatedRunContext（`ctx.deps`のみ、`ctx.retry()`等は未サポート）

**使用要件**:
- ⚠️ Agent作成後に`set_agent_toolsets()`の手動呼び出しが必要
- ⚠️ 実験的機能使用時は`ClaudeCodeCLIAgent` + `enable_experimental_deps=True`が必要

詳細は：
- [カスタムツールガイド](https://pydantic-claude-cli.readthedocs.io/ja/latest/custom-tools.html)
- [実験的依存性サポート](https://pydantic-claude-cli.readthedocs.io/ja/latest/experimental-deps.html)
- [examples/custom_tools_basic.py](examples/custom_tools_basic.py)
- [examples/experimental_deps_basic.py](examples/experimental_deps_basic.py)

### 組み込みツールの制御

Claude Code CLIの組み込みツール（WebSearch、Edit等）を柔軟に制御できます：

#### パターン1: プリセットを使用（推奨）

```python
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel, ToolPreset

# Web検索を有効化
model = ClaudeCodeCLIModel(
    'claude-haiku-4-5',
    tool_preset=ToolPreset.WEB_ENABLED
)
agent = Agent(model)

result = agent.run_sync('2025年10月25日時点で、日本の内閣総理大臣を教えてください')
# → WebSearchが使える
```

**利用可能なプリセット**:
- `ToolPreset.WEB_ENABLED` - Web検索とコンテンツ取得
- `ToolPreset.READ_ONLY` - ファイル読み込みのみ
- `ToolPreset.SAFE` - 読み込み + Web（Bashなし）
- `ToolPreset.ALL` - すべての組み込みツール

#### パターン2: BuiltinTools定数を使用

```python
from pydantic_claude_cli import ClaudeCodeCLIModel, BuiltinTools

model = ClaudeCodeCLIModel(
    'claude-haiku-4-5',
    allowed_tools=BuiltinTools.WEB_TOOLS  # ["WebSearch", "WebFetch"]
)
```

**利用可能な定数**:
- `BuiltinTools.WEB_TOOLS` - `["WebSearch", "WebFetch"]`
- `BuiltinTools.FILE_READ_TOOLS` - `["Read", "Glob", "Grep"]`
- `BuiltinTools.FILE_WRITE_TOOLS` - `["Write", "Edit"]`
- `BuiltinTools.FILE_TOOLS` - すべてのファイル操作
- `BuiltinTools.CODE_TOOLS` - `["Bash", "Task"]`

#### パターン3: 文字列で直接指定

```python
model = ClaudeCodeCLIModel(
    'claude-haiku-4-5',
    allowed_tools=["WebSearch", "WebFetch", "Read"]
)
```

#### パターン4: カスタムツールと組み込みツールの併用

```python
model = ClaudeCodeCLIModel(
    'claude-sonnet-4-5-20250929',
    tool_preset=ToolPreset.WEB_ENABLED  # ベース設定
)
agent = Agent(model)
model.set_agent_toolsets(agent._function_toolset)

@agent.tool_plain
def calculate(x: int, y: int) -> int:
    return x + y

# カスタムツール + WebSearchの両方が使える
```

#### 重要な注意事項

**ツール使用はモデルの判断に依存**:
- `allowed_tools`はツールの「許可」であり、「強制」ではありません
- モデルが自律的に「使う/使わない」を判断します
- より確実にツールを使わせるには：
  - **Sonnetモデルを推奨**（Haikuはツール判断が弱い）
  - **明示的な指示**：instructions や質問に「必ずWebSearchを使用」と記載
  - **permission_mode="acceptEdits"**：ツール使用を自動承認

例：
```python
model = ClaudeCodeCLIModel(
    'claude-sonnet-4-5-20250929',  # Sonnet推奨
    tool_preset=ToolPreset.WEB_ENABLED,
    permission_mode='acceptEdits'  # 自動承認
)
agent = Agent(
    model,
    instructions='必要に応じてWebSearchツールを使用してください'  # 明示的指示
)
result = agent.run_sync('質問内容。必ずWebSearchを使用してください')  # 明示的要求
```

**実用例**:
- [examples/read_search_write.py](examples/read_search_write.py) - Read + WebSearch + Writeの統合例
- [examples/websearch_with_preset.py](examples/websearch_with_preset.py) - ToolPreset使用例
- [examples/websearch_with_builtin_tools.py](examples/websearch_with_builtin_tools.py) - BuiltinTools使用例

### エラーハンドリング

```python
from pydantic_claude_cli import (
    ClaudeCodeCLIModel,
    ClaudeCLINotFoundError,
    ClaudeCLIProcessError,
    MessageConversionError,
)

try:
    model = ClaudeCodeCLIModel('claude-haiku-4-5')
    agent = Agent(model)
    result = agent.run_sync('こんにちは')
except ClaudeCLINotFoundError:
    print('Claude CLIが見つかりません。インストールしてください。')
except ClaudeCLIProcessError as e:
    print(f'CLIプロセスが失敗しました: {e}')
except MessageConversionError as e:
    print(f'メッセージ変換に失敗しました: {e}')
```

## 利用可能なモデル

Claude Code CLIがサポートするすべてのClaudeモデルを使用できます：

### 推奨モデル

- **`claude-haiku-4-5`** （Claude Sonnet 4.5）- 推奨
  - 高度な推論と分析能力を備えた改善されたパフォーマンス
  - 入力: $3.0/百万トークン、出力: $15.0/百万トークン

- **`claude-haiku-4-5`** （Claude Haiku 4.5）
  - 高速で効率的、クイックレスポンスに最適
  - 入力: $0.8/百万トークン、出力: $4.0/百万トークン

- **`claude-opus-4-1`** （Claude Opus 4.1）
  - 深い思考を必要とする複雑なタスクに最も有能
  - 入力: $15.0/百万トークン、出力: $75.0/百万トークン

完全なリストは[Anthropicのドキュメント](https://docs.anthropic.com/en/docs/about-claude/models)をご覧ください。

## 制限事項

これは初期実装で、以下の制限があります：

### 未対応機能

- ⚠️ **RunContextのすべての機能** - `ctx.retry()`, `ctx.run_step`等は未サポート（実験的deps機能でdepsのみ利用可能）
- ❌ **非シリアライズ可能な依存性** - httpx.AsyncClient、DB接続等は未サポート（設定のみ渡してツール内で再作成可能）
- ❌ **マルチモーダルコンテンツ** - 画像、ファイル、その他メディア未対応
- ❌ **ストリーミングレスポンス** - 現在は非ストリーミングリクエストのみ

### 対応済み機能

- ✅ **テキストベースのQ&A** - テキスト会話をサポート
- ✅ **カスタムツール（基本機能）** - 依存性なしツールが動作
- ✅ **システムプロンプト** - モデルへのカスタム指示
- ✅ **会話履歴** - マルチターン会話
- ✅ **エラーハンドリング** - 包括的なエラーメッセージ
- ✅ **使用量トラッキング** - トークン使用量とコスト情報
- ✅ **ロギング** - 標準ライブラリlogging、Pydantic Logfire対応

## トラブルシューティング

### 「Claude CLIが見つかりません」

Claude Code CLIがインストールされているか確認：

```bash
npm install -g @anthropic-ai/claude-code
claude --version
```

### 「認証に失敗しました」

Claude Codeにログイン：

```bash
claude login
```

### 「権限が拒否されました」

CLIに権限が必要な場合があります。`permission_mode='acceptEdits'`で実行してみてください：

```python
model = ClaudeCodeCLIModel(
    'claude-haiku-4-5',
    permission_mode='acceptEdits'
)
```

## 開発

### セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/pydantic-claude-cli.git
cd pydantic-claude-cli

# 開発用依存関係を含めてインストール
uv sync --all-groups

# テスト実行
uv run pytest

# サンプル実行
uv run python examples/basic_usage.py
```

### サンプルスクリプト

`examples/`ディレクトリには、以下の実用的なサンプルがあります：

1. **`basic_usage.py`** - 基本的な使い方
   - モデルの作成とAgent実行
   - シンプルなQ&A

2. **`error_handling.py`** - エラーハンドリング
   - CLI未検出エラー
   - プロセスエラー
   - 例外処理パターン

3. **`custom_tools_basic.py`** - カスタムツールの基本
   - 依存性なしツールの定義
   - ツール呼び出しの確認
   - 複数ツールの連携

4. **`custom_tools_advanced.py`** - カスタムツールの高度な例
   - Pydanticモデルを引数に取るツール
   - 非同期ツール
   - 複雑なデータ処理

5. **`logfire_basic.py`** - Pydantic Logfire基本例
   - Logfireインストルメンテーション
   - トレースの確認
   - テストモード（send_to_logfire=False）

6. **`logfire_with_custom_tools.py`** - Logfire + カスタムツール
   - カスタムツールのトレーシング
   - ツール内でのlogfire.info()使用
   - 複数ツール連携のトレース

7. **`websearch_with_preset.py`** - ToolPresetを使ったWeb検索
   - ToolPreset.WEB_ENABLEDの使用
   - WebSearchツールによる最新情報取得

8. **`websearch_with_builtin_tools.py`** - BuiltinTools定数の使用
   - BuiltinTools.WEB_TOOLSの使用
   - 型安全なツール指定

9. **`read_search_write.py`** - Read + WebSearch + Write 統合例
   - 複数組み込みツールの連携
   - ファイル読み取り → Web検索 → ファイル書き込み
   - 実用的なワークフロー

すべてのサンプルは動作確認済みです。

### テスト実行

```bash
# 全テスト実行
uv run pytest

# カバレッジ付きで実行
uv run pytest --cov=pydantic_claude_cli

# 特定のテストファイルを実行
uv run pytest tests/test_model.py -v
```

## 関連プロジェクト

- [Pydantic AI](https://github.com/pydantic/pydantic-ai) - メインのPydantic AIフレームワーク
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) - AnthropicのCLIツール
- [Claude Code SDK](https://github.com/anthropics/claude-code-sdk-python) - Claude Code用のPython SDK

---

**注意**: これは独立したプロジェクトであり、AnthropicやPydanticとは関係ありません
