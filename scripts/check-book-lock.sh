#!/bin/bash
# Book Lock Validator
# Checks if a book is locked before allowing modifications.
# Usage: ./scripts/check-book-lock.sh <book-path>
# Exit 0 = unlocked (proceed), Exit 1 = locked (stop)

BOOK_PATH="$1"

if [ -z "$BOOK_PATH" ]; then
  echo "Usage: $0 <book-path>"
  echo "Example: $0 books/longhunter-series/book-1"
  exit 1
fi

STATUS_FILE="$BOOK_PATH/STATUS.md"

if [ ! -f "$STATUS_FILE" ]; then
  echo "OK: No STATUS.md found — book is unlocked."
  exit 0
fi

if grep -q "Status: LOCKED" "$STATUS_FILE"; then
  BOOK_NAME=$(grep -oP '(?<=\*\*Book:\*\* ).*' "$STATUS_FILE" 2>/dev/null || echo "$BOOK_PATH")
  LOCKED_AT=$(grep -oP '(?<=\*\*Locked At:\*\* ).*' "$STATUS_FILE" 2>/dev/null || echo "unknown")
  REASON=$(grep -oP '(?<=\*\*Reason:\*\* ).*' "$STATUS_FILE" 2>/dev/null || echo "no reason given")
  echo "BLOCKED: Book is LOCKED."
  echo "  Book: $BOOK_NAME"
  echo "  Locked: $LOCKED_AT"
  echo "  Reason: $REASON"
  echo "  No modifications permitted."
  exit 1
else
  echo "OK: STATUS.md exists but status is not LOCKED — book is unlocked."
  exit 0
fi
