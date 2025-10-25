# Documentation Guidelines

This file provides comprehensive documentation guidelines for the pydantic-claude-cli project.

## Documentation System

Documentation is built with **Sphinx** + **MyST-Parser** (Markdown support) + **Mermaid** diagrams.

### Building Docs

```bash
cd docs
make html
# Output: docs/_build/html/index.html

# Or using uv directly
uv run sphinx-build -M html docs docs/_build
```

## Writing Guidelines

### MyST Syntax

Write all documentation in [MyST](https://mystmd.org/guide) format (Markdown for Sphinx).

**Supported extensions**:
- `colon_fence` - Directive syntax using `:::`
- `substitution` - Variable substitution
- `tasklist` - Task lists with `[ ]` and `[x]`
- `attrs_inline` - Inline attributes
- `deflist` - Definition lists

**Common MyST patterns**:

```markdown
# Table of contents
```{contents}
:depth: 2
:local:
```

# Admonitions
```{note}
This is a note.
```

# Code blocks with line numbers
```{code-block} python
:linenos:
def example():
    pass
```
```

### Tone and Style

**Avoid**:
- ❌ Exaggerated expressions: "revolutionary", "groundbreaking", "amazing"
- ❌ Marketing language: "best-in-class", "cutting-edge", "next-generation"
- ❌ Absolute terms: "完全サポート" (complete support), "必ず" (always), "絶対" (absolutely)
- ❌ Exclamation marks: "！" for professional tone
- ❌ Internal terminology: "Phase 1", "Milestone 3" (use "v0.2+" instead)
- ❌ Internal references: "Article 3", "Article 8" (refer to concepts directly instead)

**Prefer**:
- ✅ Factual descriptions: "supports", "provides", "enables"
- ✅ Qualified statements: "in most cases", "typically", "generally"
- ✅ Version-based terms: "v0.2+", "since v0.3", "as of v0.2"
- ✅ Clear, concise technical writing

### Emphasis

Use `**bold**` sparingly, only when truly necessary:
- Section headings (automatic)
- Critical warnings or requirements
- Key terms on first use

**Avoid over-emphasis**:
```markdown
# ❌ Too much bold
**This library** provides **excellent support** for **all features**.

# ✅ Appropriate bold
This library provides support for custom tools. **Note**: API key is required.
```

### Code Block Highlighting

Be careful with syntax highlighter errors to avoid build warnings.

**Common pitfalls**:

#### TOML
```toml
# ❌ Don't use null in TOML
key = null

# ✅ Use comments instead
# key = (not set)
```

#### JSON
```json
// ❌ Don't use ellipsis
{
  "items": [...]
}

// ✅ Use comments or show full structure
{
  "items": ["item1", "item2"]
}
```

#### Unknown lexers
```text
# ❌ Using unsupported lexer
```unknownlang
code here
```

# ✅ Use 'text' or 'bash'
```text
code here
```
```

#### Special characters
```python
# ❌ Avoid arrow symbols in code blocks
result → value  # May cause highlighting errors

# ✅ Use standard ASCII
result = value
```

## Structure Guidelines

### File Organization

```
docs/
├── index.md              # Main landing page
├── user-guide.md         # Getting started guide
├── custom-tools.md       # Feature-specific docs
├── experimental-deps.md  # Experimental features
├── how-it-works.md       # Technical details
├── architecture.md       # System design
└── conf.py              # Sphinx configuration
```

### Document Sections

Standard sections for feature documentation:

1. **Overview** - Brief introduction (2-3 sentences)
2. **Quick Start** - Minimal working example
3. **Features** - Detailed feature list
4. **Limitations** - Known constraints
5. **Troubleshooting** - Common issues and solutions
6. **FAQ** - Frequently asked questions
7. **Examples** - Links to example code

### Cross-References

Use MyST cross-reference syntax:

```markdown
# Link to another document
[Custom Tools](custom-tools.md)

# Link to a section
[Installation](#installation)

# Link with custom text
See the [custom tools guide](custom-tools.md) for details.
```

## Version Documentation

### Feature Status Labels

Use these labels to indicate feature maturity:

- **v0.2+** - Available since version 0.2
- **Experimental** - Working but may change
- **Deprecated** - Will be removed in future
- **Planned** - Not yet implemented

**Example**:
```markdown
## Custom Tools (v0.2+)

### Basic Tools
Dependency-free tools are supported (v0.2+).

### RunContext Support (Experimental)
Serializable dependencies are supported as an experimental feature.
```

### Version-Specific Notes

When documenting version-specific behavior:

```markdown
**Version Support**:
- v0.1: Basic agent support only
- v0.2+: Custom tools (dependency-free)
- v0.2+ (Experimental): RunContext with serializable deps
```

## Common Warnings to Avoid

Based on Sphinx build output, avoid these patterns:

1. **Missing cross-references**
   ```markdown
   # ❌ Broken link
   [Non-existent file](missing.md)

   # ✅ Valid link
   [Existing file](user-guide.md)
   ```

2. **Empty sections before transitions**
   ```markdown
   # ❌ Empty section
   ### Section Title

   ---

   # ✅ Add content
   ### Section Title

   Content here.

   ---
   ```

3. **Missing toctree entries**
   - All documentation files should be included in `index.md`'s toctree
   - Check build output for "document isn't included in any toctree"

4. **Heading level skips**
   ```markdown
   # ❌ Skip heading levels
   # Heading 1
   ### Heading 3  # Skipped level 2

   # ✅ Sequential levels
   # Heading 1
   ## Heading 2
   ### Heading 3
   ```

## Build Verification

### Before Committing

Always build documentation before committing:

```bash
uv run sphinx-build -M html docs docs/_build
```

**Check for**:
- ❌ Errors (must fix)
- ⚠️ Warnings (should fix)
- ✅ Success message

### Clean Build

For a fresh build without cache:

```bash
rm -rf docs/_build
uv run sphinx-build -M html docs docs/_build
```

## Configuration

### Sphinx Configuration

Key settings in `docs/conf.py`:

```python
# Project info
project = 'pydantic-claude-cli'
language = 'ja'  # Japanese documentation

# Extensions
extensions = [
    'myst_parser',           # Markdown support
    'sphinx.ext.autodoc',    # Auto-generate docs from docstrings
    'sphinx.ext.napoleon',   # Google-style docstrings
    'sphinxcontrib.mermaid', # Mermaid diagrams
]

# MyST configuration
myst_enable_extensions = [
    'colon_fence',
    'substitution',
    'tasklist',
    'attrs_inline',
    'deflist',
]
```

## References

- [MyST Parser Documentation](https://mystmd.org/guide)
- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [Mermaid Diagram Syntax](https://mermaid.js.org/)
- [Claude Code Memory System](https://docs.claude.com/ja/docs/claude-code/memory)
