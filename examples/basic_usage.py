"""pydantic-claude-cliの基本的な使用例

この例では、APIキーなしでClaudeモデルと対話するために、
Pydantic AIでClaudeCodeCLIModelを使用する方法を示します。

必要要件:
    - Claude Code CLIのインストール: npm install -g @anthropic-ai/claude-code
    - Claude Codeへのログイン

実行方法:
    uv run python examples/basic_usage.py
"""

import asyncio

from pydantic_ai import Agent

from pydantic_claude_cli import ClaudeCodeCLIModel


async def main():
    """ClaudeCodeCLIModelを使用した基本的な例を実行"""
    print("ClaudeCodeCLIModelを作成中...")

    # モデルインスタンスを作成
    # APIキー不要！
    model = ClaudeCodeCLIModel("claude-haiku-4-5")

    # モデルを使用してAgentを作成
    agent = Agent(
        model,
        instructions="あなたは親切なアシスタントです。簡潔に答えてください。",
    )

    print("\nClaudeにリクエストを送信中...")

    try:
        # シンプルなクエリを実行
        result = await agent.run(
            "こんにちは！プログラミングについての短いジョークを教えてください。"
        )

        print("\n" + "=" * 60)
        print("Claudeからの応答:")
        print("=" * 60)
        # AgentRunResultのoutput属性を取得
        print(result.output)
        print("=" * 60)

        # 使用情報が利用可能な場合は表示
        if hasattr(result, "all_messages") and result.all_messages():
            messages = result.all_messages()
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, "usage"):
                    print(f"\n使用量: {last_message.usage}")

    except Exception as e:
        print(f"\nエラー: {e}")
        print("\n確認事項:")
        print(
            "1. Claude Code CLIがインストールされているか: npm install -g @anthropic-ai/claude-code"
        )
        print("2. Claude Codeにログインしているか")
        raise


if __name__ == "__main__":
    asyncio.run(main())
