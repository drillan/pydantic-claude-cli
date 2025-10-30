#!/bin/bash
# Issue一覧を表示するスクリプト

echo "=== Open Issues ==="
echo ""

for file in issues/[0-9]*.md; do
    if [ -f "$file" ]; then
        # ファイルからメタデータを抽出
        title=$(head -n 1 "$file" | sed 's/^# //')
        status=$(grep "^\*\*Status\*\*:" "$file" | sed 's/^\*\*Status\*\*: //')
        priority=$(grep "^\*\*Priority\*\*:" "$file" | sed 's/^\*\*Priority\*\*: //')
        labels=$(grep "^\*\*Labels\*\*:" "$file" | sed 's/^\*\*Labels\*\*: //')

        # Openなissueのみ表示（デフォルト）
        if [ "$1" = "--all" ] || [ "$status" = "Open" ]; then
            echo "$title"
            echo "  Status: $status"
            echo "  Priority: $priority"
            echo "  Labels: $labels"
            echo ""
        fi
    fi
done

if [ "$1" = "--help" ]; then
    echo "Usage: ./issues/list.sh [--all]"
    echo ""
    echo "Options:"
    echo "  --all    Show all issues (including closed)"
    echo "  --help   Show this help message"
fi
