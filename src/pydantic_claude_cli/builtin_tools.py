"""組み込みツール定数

Claude Code CLIの組み込みツールを型安全に参照するための定数クラス。
"""

from __future__ import annotations

from enum import Enum


class BuiltinTools:
    """組み込みツールの定数

    Claude Code CLIが提供する組み込みツールの名前を定数として定義。
    文字列タイポを防ぎ、IDE補完を有効化します。

    Example:
        >>> from pydantic_claude_cli import ClaudeCodeCLIModel, BuiltinTools
        >>> model = ClaudeCodeCLIModel(
        ...     "claude-sonnet-4-5-20250929",
        ...     allowed_tools=BuiltinTools.WEB_TOOLS
        ... )
    """

    # 個別ツール定数
    BASH = "Bash"
    """Bashコマンド実行ツール"""

    READ = "Read"
    """ファイル読み込みツール"""

    WRITE = "Write"
    """ファイル書き込みツール"""

    EDIT = "Edit"
    """ファイル編集ツール"""

    GLOB = "Glob"
    """ファイル検索ツール（glob パターン）"""

    GREP = "Grep"
    """コード検索ツール（正規表現）"""

    WEB_FETCH = "WebFetch"
    """Web コンテンツ取得ツール"""

    WEB_SEARCH = "WebSearch"
    """Web 検索ツール"""

    TASK = "Task"
    """タスク実行ツール"""

    # グループ定義（よく使うツールのセット）
    WEB_TOOLS: list[str] = [WEB_SEARCH, WEB_FETCH]
    """Web関連ツール（WebSearch + WebFetch）"""

    FILE_READ_TOOLS: list[str] = [READ, GLOB, GREP]
    """ファイル読み込み系ツール"""

    FILE_WRITE_TOOLS: list[str] = [WRITE, EDIT]
    """ファイル書き込み系ツール"""

    FILE_TOOLS: list[str] = [READ, WRITE, EDIT, GLOB, GREP]
    """すべてのファイル操作ツール"""

    CODE_TOOLS: list[str] = [BASH, TASK]
    """コード実行系ツール"""

    ALL_TOOLS: list[str] = [
        BASH,
        READ,
        WRITE,
        EDIT,
        GLOB,
        GREP,
        WEB_FETCH,
        WEB_SEARCH,
        TASK,
    ]
    """すべての組み込みツール"""


class ToolPreset(str, Enum):
    """よく使うツール設定のプリセット

    頻繁に使われるツールの組み合わせをプリセットとして定義。
    ClaudeCodeCLIModelのtool_presetパラメータで使用します。

    Example:
        >>> from pydantic_claude_cli import ClaudeCodeCLIModel, ToolPreset
        >>> model = ClaudeCodeCLIModel(
        ...     "claude-sonnet-4-5-20250929",
        ...     tool_preset=ToolPreset.WEB_ENABLED
        ... )
    """

    NONE = "none"
    """組み込みツールを使用しない（カスタムツールのみ）"""

    WEB_ENABLED = "web"
    """Web検索とコンテンツ取得を有効化（WebSearch + WebFetch）"""

    READ_ONLY = "read"
    """読み取り専用ツールを有効化（Read + Glob + Grep）"""

    SAFE = "safe"
    """安全なツールのみ有効化（Read系 + Web系、Bashなし）"""

    ALL = "all"
    """すべての組み込みツールを有効化"""

    def get_allowed_tools(self) -> list[str]:
        """プリセットに対応するツールリストを取得

        Returns:
            許可するツールのリスト
        """
        if self == ToolPreset.NONE:
            return []
        elif self == ToolPreset.WEB_ENABLED:
            return BuiltinTools.WEB_TOOLS
        elif self == ToolPreset.READ_ONLY:
            return BuiltinTools.FILE_READ_TOOLS
        elif self == ToolPreset.SAFE:
            return BuiltinTools.FILE_READ_TOOLS + BuiltinTools.WEB_TOOLS
        elif self == ToolPreset.ALL:
            return BuiltinTools.ALL_TOOLS
        else:
            return []
