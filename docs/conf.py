# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "pydantic-claude-cli"
copyright = "2025, driller"
author = "driller"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinxcontrib.mermaid",
]

# MyST Parser の設定
myst_enable_extensions = [
    "colon_fence",  # ::: で始まるディレクティブ
    "deflist",  # 定義リスト
    "tasklist",  # タスクリスト
    "substitution",  # 変数置換
    "attrs_inline",  # インライン属性
]

# MyST で解析するファイルの拡張子
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "README.md"]

# 言語設定
language = "ja"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = []  # _staticディレクトリがない場合のエラーを回避

# Read the Docs テーマのオプション
html_theme_options = {
    "navigation_depth": 4,
    "titles_only": False,
}
