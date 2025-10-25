"""pydantic-claude-cliのエラーハンドリング例

この例では、ClaudeCodeCLIModelを使用する際に発生する可能性のある
さまざまなエラーの処理方法を示します。

実行方法:
    uv run python examples/error_handling.py
"""

import asyncio

from pydantic_ai import Agent

from pydantic_claude_cli import (
    ClaudeCLINotFoundError,
    ClaudeCLIProcessError,
    ClaudeCodeCLIModel,
    MessageConversionError,
)


async def example_cli_not_found():
    """CLI未検出エラーの処理を実演"""
    print("\n" + "=" * 60)
    print("例: CLIが見つからない")
    print("=" * 60)

    try:
        # 存在しないCLIパスでモデルを作成しようとする
        model = ClaudeCodeCLIModel(
            "claude-haiku-4-5", cli_path="/non/existent/path/to/claude"
        )
        agent = Agent(model)
        await agent.run("こんにちは")
    except ClaudeCLINotFoundError as e:
        print(f"予期されたエラーをキャッチ: {e}")
        print("\nこのエラーは、Claude CLIが見つからない場合に発生します。")


async def example_basic_request():
    """成功するリクエストを実演"""
    print("\n" + "=" * 60)
    print("例: 成功するリクエスト")
    print("=" * 60)

    try:
        model = ClaudeCodeCLIModel("claude-haiku-4-5")
        agent = Agent(model, instructions="非常に簡潔に答えてください。")

        result = await agent.run("2+2は？数字だけ答えてください。")
        print(f"成功！ 応答: {result.output}")

    except ClaudeCLINotFoundError as e:
        print(f"CLIが見つかりません: {e}")
        print("まずClaude Code CLIをインストールしてください。")
    except ClaudeCLIProcessError as e:
        print(f"CLIプロセスエラー: {e}")
    except MessageConversionError as e:
        print(f"メッセージ変換エラー: {e}")
    except Exception as e:
        print(f"予期しないエラー: {e}")


async def main():
    """すべてのエラーハンドリング例を実行"""
    print("pydantic-claude-cliのエラーハンドリング例")
    print("=" * 60)

    # 例を実行
    await example_cli_not_found()
    await example_basic_request()

    print("\n" + "=" * 60)
    print("例の実行完了！")
    print("=" * 60)
    print(
        "\n📝 Note: カスタムツールの使用例は examples/custom_tools_basic.py を参照してください。"
    )


if __name__ == "__main__":
    asyncio.run(main())
