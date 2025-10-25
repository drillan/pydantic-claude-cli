"""Read + WebSearch + Write の統合例

このスクリプトは、組み込みツールを組み合わせた実用的なユースケースを示します。

ユースケース:
1. ToDoファイルを読み取る（Read）
2. ToDoの内容に基づいてWeb検索（WebSearch）
3. 検索結果をファイルに書き込む（Write）

実行方法:
    uv run python examples/read_search_write.py
"""

import asyncio
import tempfile
from pathlib import Path

from pydantic_ai import Agent

from pydantic_claude_cli import BuiltinTools, ClaudeCodeCLIModel


async def main() -> None:
    """Read + WebSearch + Write の統合例を実行"""

    print("=" * 60)
    print("Read + WebSearch + Write 統合例")
    print("=" * 60)
    print()

    # 一時ディレクトリを作成
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        todo_file = tmpdir_path / "todo.txt"
        result_file = tmpdir_path / "result.txt"

        # ステップ1: ToDoファイルを作成
        print("【ステップ1】ToDoファイルを作成")
        todo_content = """ToDo リスト

1. ToDo: 2025年10月25日時点の日本の内閣総理大臣を調べて入力
2. ToDo: その人の経歴を簡単にまとめる
"""
        todo_file.write_text(todo_content, encoding="utf-8")
        print(f"ファイル作成: {todo_file}")
        print(f"内容:\n{todo_content}")
        print()

        # ステップ2: モデルとエージェントを設定
        print("【ステップ2】モデルとエージェントを設定")
        print("有効化するツール: Read + Write + WebSearch + WebFetch")
        print()

        # Read + Write + WebSearchツールを有効化
        model = ClaudeCodeCLIModel(
            "claude-sonnet-4-5-20250929",
            allowed_tools=BuiltinTools.WEB_TOOLS + BuiltinTools.FILE_TOOLS,
            permission_mode="acceptEdits",  # ツール使用を自動承認
        )

        agent = Agent(
            model,
            instructions=f"""あなたはToDoリストを処理するアシスタントです。

作業ディレクトリ: {tmpdir}

以下のツールを使用してタスクを完了してください:
- Readツール: ファイル内容を読み取る
- WebSearchツール: 最新情報を検索する
- Writeツール: 結果をファイルに書き込む

必ず以下の手順で実行してください:
1. {todo_file}を読み取る
2. ToDoの内容に基づいてWebSearchで最新情報を検索
3. 検索結果を{result_file}に書き込む

ファイルパスは必ず絶対パスを使用してください。
""",
        )

        # ステップ3: タスクを実行
        print("【ステップ3】エージェントにタスクを依頼")
        print()

        result = await agent.run(
            f"""以下のタスクを実行してください:

1. {todo_file}を読み取る
2. ファイルに書かれているToDoに従って、WebSearchで最新情報を検索
3. 検索結果を{result_file}に書き込む

必ず上記3つのツールを使用してください。"""
        )

        print("=" * 60)
        print("エージェントの応答:")
        print("=" * 60)
        print(result.output)
        print()

        # ステップ4: 結果を確認
        print("=" * 60)
        print("【ステップ4】結果ファイルを確認")
        print("=" * 60)

        if result_file.exists():
            result_content = result_file.read_text(encoding="utf-8")
            print(f"ファイル: {result_file}")
            print(f"内容:\n{result_content}")
            print()
            print("✅ Read → WebSearch → Write の流れが成功！")
        else:
            print(f"⚠️ 結果ファイルが作成されませんでした: {result_file}")
            print("エージェントがWriteツールを使用しなかった可能性があります。")

        print()
        print("=" * 60)

        # 使用状況
        usage = result.usage()
        print("使用状況:")
        print(f"  入力トークン: {usage.input_tokens:,}")
        print(f"  出力トークン: {usage.output_tokens:,}")
        print(f"  合計トークン: {usage.total_tokens:,}")
        print()

        print("=" * 60)
        print("このサンプルで使用した組み込みツール:")
        print("  - Read: ファイル読み取り")
        print("  - WebSearch: Web検索")
        print("  - Write: ファイル書き込み")
        print()
        print("allowed_toolsの設定:")
        print(f"  {BuiltinTools.WEB_TOOLS + BuiltinTools.FILE_TOOLS}")
        print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n中断されました")
    except Exception as e:
        print(f"\n\n❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
