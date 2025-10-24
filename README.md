# pydantic-claude-cli

**Pydantic AI用のClaude Code CLIアダプター** - APIキー不要でClaudeモデルを使用！

このパッケージを使用すると、[Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)を介して[Pydantic AI](https://ai.pydantic.dev/)でClaudeモデルを使用でき、Anthropic APIキーが不要になります。

## 特徴

- ✅ **APIキー不要** - Claude Code CLIで認証
- ✅ **簡単統合** - Pydantic AIモデルのドロップイン置き換え
- ✅ **テキストベース会話** - テキストチャットを完全サポート
- ✅ **カスタムツール** - 依存性なしツールを完全サポート（v0.2+）
- ⚠️ **マルチモーダル** - 画像/ファイル未対応（近日対応予定）

## 必要要件

1. **Node.js** - Claude Code CLIに必要
2. **Claude Code CLI** - インストールと認証が必要
3. **Python 3.10+** - Pydantic AI実行用

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
uv add pydantic-claude-cli

# またはpip使用
pip install pydantic-claude-cli
```

## クイックスタート

```python
import asyncio
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

async def main():
    # モデルインスタンス作成 - APIキー不要！
    model = ClaudeCodeCLIModel('claude-sonnet-4-5-20250929')

    # Pydantic AI Agentで使用
    agent = Agent(
        model,
        instructions='あなたは親切なアシスタントです。'
    )

    # クエリ実行
    result = await agent.run('こんにちは、Claude！')
    print(result.output)

if __name__ == '__main__':
    asyncio.run(main())
```

## 使用例

### 基本的な会話

```python
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

model = ClaudeCodeCLIModel('claude-sonnet-4-5-20250929')
agent = Agent(model, instructions='簡潔で親切に答えてください。')

result = await agent.run('量子コンピューティングを一文で説明してください。')
print(result.output)
```

### カスタム設定

```python
from pydantic_claude_cli import ClaudeCodeCLIModel

model = ClaudeCodeCLIModel(
    'claude-sonnet-4-5-20250929',
    max_turns=10,  # 会話ターン数を制限
    permission_mode='acceptEdits',  # 編集を自動承認
    cli_path='/custom/path/to/claude',  # カスタムCLIパス
)
```

### カスタムツールの使用（v0.2+）

依存性なしツール（`@agent.tool_plain`）が**完全に動作します**：

```python
from pydantic_ai import Agent
from pydantic_claude_cli import ClaudeCodeCLIModel

model = ClaudeCodeCLIModel('claude-sonnet-4-5-20250929')
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
result = await agent.run('100円、200円、300円の合計を通貨形式で表示して')
print(result.output)
```

**重要**: `model.set_agent_toolsets(agent._function_toolset)` の呼び出しが必要です。

**サポート機能**:
- ✅ 基本型のツール（int, str, float, bool, list, dict）
- ✅ Pydanticモデルを引数に取るツール
- ✅ 同期・非同期ツール
- ✅ 複数ツールの連携
- ✅ 実際のツール呼び出し確認済み

**制限事項**:
- ⚠️ `RunContext`依存ツール（`@agent.tool`）は未サポート（Phase 3で予定）
- ⚠️ Agent作成後に`set_agent_toolsets()`の手動呼び出しが必要

詳細は：
- [カスタムツールガイド](https://pydantic-claude-cli.readthedocs.io/ja/latest/custom-tools.html)
- [examples/custom_tools_basic.py](examples/custom_tools_basic.py)

### エラーハンドリング

```python
from pydantic_claude_cli import (
    ClaudeCodeCLIModel,
    ClaudeCLINotFoundError,
    ClaudeCLIProcessError,
    MessageConversionError,
)

try:
    model = ClaudeCodeCLIModel('claude-sonnet-4-5-20250929')
    agent = Agent(model)
    result = await agent.run('こんにちは！')
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

- **`claude-sonnet-4-5-20250929`** （Claude Sonnet 4.5）- 推奨
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

- ⚠️ **RunContext依存ツール** - `@agent.tool`（依存性注入）は未サポート
- ❌ **マルチモーダルコンテンツ** - 画像、ファイル、その他メディア未対応
- ❌ **ストリーミングレスポンス** - 現在は非ストリーミングリクエストのみ

### 対応済み機能

- ✅ **テキストベースのQ&A** - テキスト会話を完全サポート
- ✅ **カスタムツール（Phase 1）** - 依存性なしツールが完全動作
- ✅ **システムプロンプト** - モデルへのカスタム指示
- ✅ **会話履歴** - マルチターン会話
- ✅ **エラーハンドリング** - 包括的なエラーメッセージ
- ✅ **使用量トラッキング** - トークン使用量とコスト情報
- ✅ **ロギング** - 標準ライブラリlogging、Pydantic Logfire対応

## 動作の仕組み

標準のAnthropic API統合とは異なり、`pydantic-claude-cli`はClaude Code CLIをサブプロセスとして使用します：

1. `ClaudeCodeCLIModel`インスタンスを作成
2. クエリ実行時、Claude CLIをサブプロセスとして起動
3. stdin/stdoutを介してJSONでメッセージ交換
4. CLIがClaude Codeログインを使用して認証を処理
5. レスポンスをPydantic AI形式に変換

**APIキー不要** - Claude Code CLIが認証を処理するため！

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
    'claude-sonnet-4-5-20250929',
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
uv sync --all-extras

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

3. **`custom_tools_basic.py`** - カスタムツールの基本（v0.2+）
   - 依存性なしツールの定義
   - ツール呼び出しの確認
   - 複数ツールの連携

4. **`custom_tools_advanced.py`** - カスタムツールの高度な例（v0.2+）
   - Pydanticモデルを引数に取るツール
   - 非同期ツール
   - 複雑なデータ処理

すべてのサンプルは実際に動作確認済みです。

### テスト実行

```bash
# 全テスト実行
uv run pytest

# カバレッジ付きで実行
uv run pytest --cov=pydantic_claude_cli

# 特定のテストファイルを実行
uv run pytest tests/test_model.py -v
```

## コントリビューション

コントリビューション歓迎！改善が必要な領域：

- 🔧 ストリーミングレスポンス対応
- 🔧 カスタムツール統合
- 🔧 マルチモーダルコンテンツ対応
- 🔧 より良いエラーメッセージ
- 📚 さらなる例とドキュメント

## ライセンス

MITライセンス - 詳細はLICENSEファイルをご覧ください。

## 謝辞

- Pydanticによる[Pydantic AI](https://ai.pydantic.dev/)をベースに構築
- Anthropicによる[Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)を使用
- APIキー不要のClaude アクセスの必要性に触発されて開発

## 関連プロジェクト

- [Pydantic AI](https://github.com/pydantic/pydantic-ai) - メインのPydantic AIフレームワーク
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) - AnthropicのCLIツール
- [Claude Code SDK](https://github.com/anthropics/claude-code-sdk-python) - Claude Code用のPython SDK

---

**注意**: これは独立したプロジェクトであり、AnthropicやPydanticとは公式に提携していません。
