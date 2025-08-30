#!/usr/bin/env bash
set -euo pipefail
echo "[banlist] scanning for forbidden words…"
# пути, где ЗАПРЕЩЕНО:
PATHS="services storage workers api db"
# слова, которые запрещены в продовых модулях:
PATTERN='\b(mock|stub|placeholder|demo|sample|example|simplified)\b'
# также не допускаем оставленный "pass" в реализациях
PASS_PATTERN='^\s*pass\s*$|^\s*raise\s+NotImplementedError'
violations=0
while IFS= read -r -d '' f; do
  if grep -E -n "$PATTERN" "$f" >/dev/null; then
    echo "❌ Forbidden word in $f"
    violations=1
  fi
  if grep -E -n "$PASS_PATTERN" "$f" >/dev/null; then
    echo "❌ Found 'pass' or NotImplemented in $f"
    violations=1
  fi
done < <(git ls-files $PATHS | grep -E '\.py$' | xargs -0 printf '%s\0')
if [ $violations -ne 0 ]; then
  echo "[banlist] failed."
  exit 1
fi
echo "[banlist] ok."
