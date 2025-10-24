# 既知の問題と制限事項

## カスタムツール機能（v0.2+）

### 問題1: MCPツールが認識されない（調査中）

**症状**:
- MCPサーバーは正常に作成される（警告メッセージで確認可能）
- ツール定義は正しくMCP形式に変換される
- しかし、LLMがツールを「利用できない」と応答する
- ツールが実際に呼び出されない

**再現手順**:
```bash
uv run python examples/test_custom_tools_e2e.py
```

**期待される動作**:
- ツールの`print`文が表示される
- LLMがツールを使って計算する

**実際の動作**:
- ツールのprint文が表示されない
- LLMが直接計算で回答する

**デバッグ情報**:
```
UserWarning: Creating MCP server with 3 custom tools: [...]
UserWarning: Creating MCP server 'pydantic-custom-tools' with 3 SDK tools
UserWarning: MCP server created: type=sdk, name=pydantic-custom-tools
```

**調査済み項目**:
- ✅ `ClaudeCodeOptions.mcp_servers`は正しく設定されている
- ✅ `allowed_tools`にツール名を追加済み
- ✅ MCPサーバーのtype='sdk'で正常に作成
- ✅ `permission_mode='acceptEdits'`を設定済み

**根本原因（2025-10-24判明）**:

**Claude Code SDKの既知のバグ**（GitHub Issue #6710）:
- `create_sdk_mcp_server()`で作成したSDK MCP Serverが正常に動作しない
- Claude CLIがMCPツールを認識しない
- 複数のユーザーが同じ問題を報告

**関連Issue**:
- [Issue #6710](https://github.com/anthropics/claude-code/issues/6710): SDK MCP server fails to connect
- [Issue #3426](https://github.com/anthropics/claude-code/issues/3426): MCP tools not exposed to AI sessions
- [Issue #467](https://github.com/anthropics/claude-code/issues/467): Cannot get MCP tool calls working

**影響バージョン**:
- Claude CLI v1.0.96以降
- claude-code-sdk v0.0.25（現在使用中）

**回避策**:

現時点では、以下の方法を推奨します：

1. **Pydantic AI標準を使用**:
   ```python
   from pydantic_ai.models.anthropic import AnthropicModel

   model = AnthropicModel('claude-sonnet-4-5-20250929')
   agent = Agent(model)

   @agent.tool
   async def my_tool(ctx: RunContext[DB], x: int) -> str:
       # 完全なツールサポート
       return await ctx.deps.query(x)
   ```

2. **組み込みツール（Bash）を使用**:
   - Claude Code CLIの組み込みツールは正常に動作する

**次のステップ**:

1. **Anthropicサポートへの問い合わせ**:
   - SDK MCP Serverの正しい使い方を確認
   - 既知のバグかどうか確認

2. **通常のNode.js環境でのテスト**:
   - Claude Code外の環境でテスト
   - CI/CD環境でのE2Eテスト

3. **代替実装の検討**:
   - stdio MCPサーバーとして外部プロセスで実行
   - または、ツール実行ロジックを別の方法で統合

---

## 実装状況まとめ（2025-10-24）

### ✅ 完成している部分

- コア実装（tool_support.py, tool_converter.py）
- ツール抽出ロジック
- MCP変換ロジック
- MCPサーバー作成
- 包括的なドキュメント
- テストスイート

### ⚠️ 未解決の問題

- Claude CLIがMCPツールを認識しない
- 実際のツール呼び出しが確認できない

### 💡 推奨

現時点では、この機能は**実験的機能**として扱うことを推奨します：

1. **ドキュメントに実験的機能と明記**
2. **ユーザーフィードバックを収集**
3. **通常環境でのテスト結果を待つ**
4. **動作が確認できたらベータ版としてリリース**

---

**最終更新**: 2025-10-24
