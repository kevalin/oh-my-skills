#!/usr/bin/env bash
# Quick duplicate scan: check if a URL exists in the Obsidian vault
# Usage: ./dedup.sh <url> [vault_path]

URL="${1:?Usage: $0 <url> [vault_path]}"
VAULT="${2:-$HOME/Documents/obsidian/Interpreter}"

# Normalize URL: strip tracking params
CLEAN=$(echo "$URL" | sed 's/[?&]utm_[^&]*//g; s/[?&]s=[^&]*//g; s/[?&]t=[^&]*//g; s/&$//; s/?$//')

echo "🔍 Searching for: $CLEAN"
echo "   in: $VAULT"

MATCHES=$(rg -l --fixed-strings "$CLEAN" "$VAULT" 2>/dev/null)

if [ -n "$MATCHES" ]; then
    echo "⚠️  Already exists:"
    echo "$MATCHES" | while read -r f; do
        echo "   $(basename "$f")"
    done
    exit 1
else
    # Also try x.com/twitter.com ID extraction
    POST_ID=$(echo "$URL" | grep -oP 'status/(\d+)' | cut -d/ -f2)
    if [ -n "$POST_ID" ]; then
        ID_MATCHES=$(rg -l "status/$POST_ID" "$VAULT" 2>/dev/null)
        if [ -n "$ID_MATCHES" ]; then
            echo "⚠️  Already exists (by post ID):"
            echo "$ID_MATCHES" | while read -r f; do
                echo "   $(basename "$f")"
            done
            exit 1
        fi
    fi
    echo "✅ Not found — safe to clip"
fi
