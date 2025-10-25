"""Model implementation for Claude Code CLI."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from claude_code_sdk import ClaudeSDKClient, query as claude_query
from claude_code_sdk.types import (
    AssistantMessage,
    ClaudeCodeOptions,
    Message,
    ResultMessage,
    SystemMessage,
)
from pydantic_ai import ModelProfile
from pydantic_ai.messages import ModelMessage, ModelResponse
from pydantic_ai.models import Model, ModelRequestParameters, ModelSettings

from .builtin_tools import ToolPreset
from .exceptions import (
    ClaudeCLIProcessError,
    MessageConversionError,
    ClaudeCLINotFoundError,
)
from .message_converter import (
    convert_from_claude_message,
    convert_to_claude_prompt,
    extract_system_prompt,
    extract_usage_from_result,
)
from .provider import ClaudeCodeCLIProvider

# ロガーを設定
logger = logging.getLogger(__name__)


@dataclass(init=False)
class ClaudeCodeCLIModel(Model):
    """A model that uses Claude Code CLI.

    This model enables using Claude models without an API key by leveraging
    the Claude Code CLI. The CLI must be installed on the system.

    Example:
        ```python
        from pydantic_ai import Agent
        from pydantic_claude_cli import ClaudeCodeCLIModel

        model = ClaudeCodeCLIModel('claude-3-5-sonnet-latest')
        agent = Agent(model, instructions='You are a helpful assistant')

        result = await agent.run('Hello, Claude!')
        print(result.data)
        ```

    Note:
        This initial implementation has the following limitations:
        - Only text-based messages are supported
        - Custom tools are not yet integrated
        - Multimodal content (images, files) is not yet supported
    """

    _model_name: str = field(repr=True)
    _provider: ClaudeCodeCLIProvider = field(repr=False)
    _cli_path: str | Path | None = field(default=None, repr=False)
    _max_turns: int | None = field(default=None, repr=False)
    _permission_mode: (
        Literal["default", "acceptEdits", "plan", "bypassPermissions"] | None
    ) = field(default=None, repr=False)
    _agent_toolsets: Any = field(
        default=None, repr=False
    )  # Agent._function_toolsetへの参照
    _enable_experimental_deps: bool = field(default=False, repr=False)
    _tool_preset: ToolPreset | str | None = field(default=None, repr=False)
    _allowed_tools: list[str] | None = field(default=None, repr=False)
    _disallowed_tools: list[str] | None = field(default=None, repr=False)

    def __init__(
        self,
        model_name: str,
        *,
        provider: Literal["claude-code-cli"]
        | ClaudeCodeCLIProvider = "claude-code-cli",
        profile: ModelProfile | None = None,
        settings: ModelSettings | None = None,
        cli_path: str | Path | None = None,
        max_turns: int | None = None,
        permission_mode: Literal["default", "acceptEdits", "plan", "bypassPermissions"]
        | None = None,
        enable_experimental_deps: bool = False,
        tool_preset: ToolPreset | str | None = None,
        allowed_tools: list[str] | None = None,
        disallowed_tools: list[str] | None = None,
    ):
        """Initialize Claude Code CLI model.

        Args:
            model_name: Name of the Claude model to use (e.g., 'claude-3-5-sonnet-latest').
            provider: Provider instance or 'claude-code-cli' string.
            profile: Model profile to use.
            settings: Default model settings.
            cli_path: Optional custom path to Claude CLI executable.
            max_turns: Maximum number of conversation turns (passed to CLI).
            permission_mode: Permission mode for the CLI.
            enable_experimental_deps: Enable experimental dependency injection support (Milestone 3).
            tool_preset: Preset tool configuration (e.g., ToolPreset.WEB_ENABLED).
                This is applied as a base, and allowed_tools/disallowed_tools can further customize it.
                Examples: ToolPreset.WEB_ENABLED, ToolPreset.SAFE, "web"
            allowed_tools: List of tool names to allow. None means default behavior (minimal permissions).
                Examples: ["WebSearch", "WebFetch", "Read"]
            disallowed_tools: List of tool names to disallow.
                Examples: ["Bash", "Write", "Edit"]
                If both allowed_tools and disallowed_tools are specified,
                disallowed_tools takes precedence (security first).
        """
        self._model_name = model_name
        self._cli_path = cli_path
        self._max_turns = max_turns
        self._permission_mode = permission_mode
        self._enable_experimental_deps = enable_experimental_deps
        self._tool_preset = tool_preset
        self._allowed_tools = allowed_tools
        self._disallowed_tools = disallowed_tools

        if isinstance(provider, str):
            if provider == "claude-code-cli":
                provider = ClaudeCodeCLIProvider(cli_path=cli_path)
            else:
                raise ValueError(f"Unknown provider string: {provider}")

        self._provider = provider

        # Get profile from provider if not specified
        if profile is None and hasattr(self._provider, "model_profile"):
            profile = self._provider.model_profile(model_name)

        super().__init__(settings=settings, profile=profile)

    @property
    def model_name(self) -> str:
        """The model name."""
        return self._model_name

    @property
    def system(self) -> str:
        """The model system/provider name."""
        return self._provider.name

    def set_agent_toolsets(self, toolsets: Any) -> None:
        """Agentのtoolsetsを設定する（内部使用）

        この関数は、Agent作成後に自動的に呼び出されることを想定しています。
        ユーザーが直接呼び出す必要はありません。

        Args:
            toolsets: Agent._function_toolset

        Note:
            これはPydantic AIの公式APIではなく、内部実装の詳細に依存しています。
            将来のバージョンで変更される可能性があります。
        """
        self._agent_toolsets = toolsets

    def _resolve_tools(
        self,
        custom_tool_names: list[str],
    ) -> tuple[list[str], list[str]]:
        """ツール設定を解決する

        Args:
            custom_tool_names: カスタムツール名のリスト（MCPツール名）

        Returns:
            (final_allowed, final_disallowed): 最終的な許可/禁止ツールのリスト

        Note:
            優先順位: tool_preset → allowed_tools → disallowed_tools
            - tool_presetがベースとなる
            - allowed_toolsで追加/上書き
            - disallowed_toolsで除外（最優先）
        """
        # Step 0: tool_presetから基本ツールリストを取得
        preset_tools: list[str] = []
        if self._tool_preset:
            if isinstance(self._tool_preset, str):
                preset = ToolPreset(self._tool_preset)
            else:
                preset = self._tool_preset
            preset_tools = preset.get_allowed_tools()

        allowed = self._allowed_tools
        disallowed = self._disallowed_tools

        # Step 1: ベースセットを決定
        if allowed is not None:
            # preset_tools + allowed_tools + custom_tools
            base_allowed = list(set(preset_tools + allowed + custom_tool_names))
        elif preset_tools:
            # preset_tools + custom_tools
            base_allowed = list(set(preset_tools + custom_tool_names))
        elif custom_tool_names:
            # カスタムツールのみ（デフォルト）
            base_allowed = custom_tool_names
        else:
            # 何も許可しない（最もセキュア）
            base_allowed = []

        # Step 2: disallowedで除外（セキュリティ優先）
        if disallowed:
            final_allowed = [t for t in base_allowed if t not in disallowed]
            final_disallowed = disallowed
        else:
            final_allowed = base_allowed
            # カスタムツール使用時は組み込みツールをデフォルトで無効化
            if custom_tool_names:
                final_disallowed = [
                    "Bash",
                    "Read",
                    "Write",
                    "Edit",
                    "Glob",
                    "Grep",
                    "WebFetch",
                    "WebSearch",
                    "Task",
                ]
                # ただしallowedで明示的に許可されたものは除外
                final_disallowed = [
                    t for t in final_disallowed if t not in final_allowed
                ]
            else:
                final_disallowed = []

        return final_allowed, final_disallowed

    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        """Make a non-streaming request to the model.

        Args:
            messages: List of messages in the conversation.
            model_settings: Optional model-specific settings.
            model_request_parameters: Request parameters including tools and output settings.

        Returns:
            Model response with generated content.

        Raises:
            MessageConversionError: If message conversion fails.
            ClaudeCLIProcessError: If the CLI process fails.
        """
        # Prepare settings
        model_settings, model_request_parameters = self.prepare_request(
            model_settings, model_request_parameters
        )

        # カスタムツールサポート（Phase 1 + Milestone 3: 依存性サポート）
        mcp_server = None
        if model_request_parameters.function_tools:
            from .tool_converter import create_mcp_from_tools
            from .tool_support import extract_tools_from_agent

            # output_toolsはサポートしない
            if model_request_parameters.output_tools:
                raise MessageConversionError(
                    "Output tools are not supported with custom tools in ClaudeCodeCLIModel. "
                    "Please use only function tools (@agent.tool or @agent.tool_plain)."
                )

            # ツールを抽出して検証
            # _agent_toolsetsがある場合は、リストとしてラップして渡す
            agent_toolsets_list = (
                [self._agent_toolsets] if self._agent_toolsets is not None else None
            )
            tools_with_funcs, has_context_tools = extract_tools_from_agent(
                model_request_parameters, agent_toolsets=agent_toolsets_list
            )

            # Milestone 3: 依存性サポート（実験的）
            deps_json: str | None = None
            deps_type_info: type | None = None
            if self._enable_experimental_deps and has_context_tools:
                from .deps_context import get_current_deps_with_type
                from .deps_support import is_serializable_deps, serialize_deps

                # ContextVarから依存性を取得（型情報も含む）
                deps_result = get_current_deps_with_type()

                if deps_result is not None:
                    deps, deps_type_info = deps_result
                    logger.info(
                        "Experimental deps support enabled, checking serializability (type: %s)",
                        deps_type_info,
                    )

                    # シリアライズ可能かチェック
                    check_type = (
                        deps_type_info if deps_type_info is not None else type(deps)
                    )
                    if not is_serializable_deps(check_type):
                        raise MessageConversionError(
                            "Non-serializable dependencies are not supported with ClaudeCodeCLIModel.\n"
                            "Only primitive types, dict, list, and Pydantic models are supported.\n\n"
                            "Non-serializable types:\n"
                            "  - httpx.AsyncClient, httpx.Client\n"
                            "  - sqlalchemy.Engine\n"
                            "  - File handles, sockets, etc.\n\n"
                            "Workaround: Use serializable configuration and recreate connections in tools."
                        )

                    # シリアライズ
                    try:
                        deps_json = serialize_deps(deps)
                        logger.info(
                            "Successfully serialized dependencies for MCP tools"
                        )
                    except ValueError as e:
                        raise MessageConversionError(
                            f"Failed to serialize dependencies: {e}"
                        ) from e
                else:
                    logger.warning(
                        "RunContext tools detected but no deps found in ContextVar. "
                        "Did you use ClaudeCodeCLIAgent?"
                    )

            # RunContext依存ツールがあり、実験的機能が無効の場合はエラー
            elif has_context_tools:
                raise MessageConversionError(
                    "Tools that require RunContext are not supported with ClaudeCodeCLIModel.\n"
                    "Only context-free tools can be used.\n\n"
                    "Supported (context-free tool):\n"
                    "  @agent.tool_plain\n"
                    "  def my_tool(x: int, y: int) -> str:\n"
                    "      return str(x + y)\n\n"
                    "Not supported (requires RunContext):\n"
                    "  @agent.tool\n"
                    "  async def my_tool(ctx: RunContext[DB], x: int) -> str:\n"
                    "      result = await ctx.deps.query(x)  # Cannot access ctx.deps\n"
                    "      return str(result)\n\n"
                    "Workaround 1: Use Pydantic AI standard (AnthropicModel) for full RunContext support.\n"
                    "Workaround 2: Enable experimental deps support with enable_experimental_deps=True (Milestone 3)."
                )

            # MCPサーバー作成（依存性を渡す）
            if tools_with_funcs:
                logger.info(
                    "Creating MCP server for %d custom tools (deps: %s, type: %s)",
                    len(tools_with_funcs),
                    deps_json is not None,
                    deps_type_info,
                )
                mcp_server = create_mcp_from_tools(
                    tools_with_funcs, deps_data=deps_json, deps_type=deps_type_info
                )
                logger.debug("MCP server created successfully")

        # Convert messages
        try:
            prompt = convert_to_claude_prompt(messages)
            system_prompt = extract_system_prompt(messages)
        except Exception as e:
            raise MessageConversionError(f"Failed to convert messages: {e}") from e

        # Prepare Claude Code options
        # カスタムツールの名前リストを作成（mcp_serverが存在する場合のみ）
        # MCPツールは "mcp__{server_name}__{tool_name}" の形式で参照される
        custom_tool_names: list[str] = []
        if mcp_server is not None:
            mcp_server_name = "custom"
            # ツール名にプレフィックスを付ける
            custom_tool_names = [
                f"mcp__{mcp_server_name}__{tool.name}"
                for tool in (model_request_parameters.function_tools or [])
            ]

        # MCPツールの許可設定
        # MCPツールは "mcp__{server_name}__{tool_name}" の形式で参照される
        # _resolve_toolsを使ってユーザー設定を反映
        final_allowed, final_disallowed = self._resolve_tools(custom_tool_names)

        options = ClaudeCodeOptions(
            model=self._model_name,
            system_prompt=system_prompt,
            max_turns=self._max_turns,
            permission_mode=self._permission_mode,
            # MCPサーバー設定（カスタムツールがある場合のみ）
            mcp_servers={"custom": mcp_server} if mcp_server else {},
            # ユーザー設定 + カスタムツールを許可
            allowed_tools=final_allowed,
            # ユーザー設定に基づいて無効化
            disallowed_tools=final_disallowed,
        )

        # MCPツールがある場合はClaudeSDKClientを使用、ない場合はquery()を使用
        # NOTE: query()関数ではSDK MCP Serverが正しく動作しない（既知の問題）
        # ClaudeSDKClientを使用すると、MCPツールが正常に呼び出される
        try:
            response_messages: list[Message] = []

            if mcp_server is not None:
                # ClaudeSDKClientを使用（MCPツール対応）
                logger.debug("Using ClaudeSDKClient for MCP tools support")
                async with ClaudeSDKClient(options=options) as client:
                    await client.query(prompt)
                    async for message in client.receive_response():
                        response_messages.append(message)
                logger.debug(
                    "Received %d messages from ClaudeSDKClient", len(response_messages)
                )
            else:
                # query()を使用（通常動作）
                logger.debug("Using query() for standard request")
                async for message in claude_query(prompt=prompt, options=options):
                    response_messages.append(message)

                    # ResultMessage is the last message, but continue to consume
                    # the generator to avoid cleanup errors
                    if isinstance(message, ResultMessage):
                        # Don't break, let the generator finish naturally
                        pass

            # Find the assistant message(s) in the response
            assistant_messages: list[AssistantMessage] = []
            result_message: ResultMessage | None = None

            for msg in response_messages:
                if isinstance(msg, AssistantMessage):
                    assistant_messages.append(msg)
                elif isinstance(msg, ResultMessage):
                    result_message = msg
                elif isinstance(msg, SystemMessage):
                    # System messages are informational, we can log them if needed
                    pass

            if not assistant_messages:
                # Check if there was an error
                if result_message and result_message.is_error:
                    raise ClaudeCLIProcessError(
                        f"Claude CLI returned error: {result_message.result or 'Unknown error'}"
                    )
                raise ClaudeCLIProcessError(
                    "No assistant message received from Claude CLI"
                )

            # Convert the last assistant message to ModelResponse
            # (in multi-turn conversations, there might be multiple)
            last_assistant_message = assistant_messages[-1]
            model_response = convert_from_claude_message(
                last_assistant_message, self._model_name
            )

            # Add usage information if available
            if result_message:
                try:
                    usage = extract_usage_from_result(
                        {
                            "usage": result_message.usage,
                            "duration_ms": result_message.duration_ms,
                            "duration_api_ms": result_message.duration_api_ms,
                            "num_turns": result_message.num_turns,
                            "total_cost_usd": result_message.total_cost_usd,
                        }
                    )
                    # Replace the default usage with extracted one
                    model_response = ModelResponse(
                        parts=model_response.parts,
                        usage=usage,
                        model_name=model_response.model_name,
                        timestamp=model_response.timestamp,
                        provider_name=model_response.provider_name,
                        finish_reason="stop"
                        if not result_message.is_error
                        else "error",
                    )
                except Exception:
                    # If usage extraction fails, continue with default usage
                    pass

            return model_response

        except Exception as e:
            # Wrap any Claude SDK exceptions
            if "CLI not found" in str(e) or "claude: command not found" in str(e):
                raise ClaudeCLINotFoundError() from e
            raise ClaudeCLIProcessError(f"Failed to query Claude CLI: {e}") from e
