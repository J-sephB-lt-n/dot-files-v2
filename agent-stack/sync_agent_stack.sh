#!/bin/bash

set -eo pipefail

if [ -n "${OPENCODE_GLOBAL_CONFIG_DIR}" ]; then
  find ./agents -name '*.md' -type f | while IFS= read -r filepath; do
    dest_filename=$(basename "$filepath")
    dest_filepath="$OPENCODE_GLOBAL_CONFIG_DIR/agents/$dest_filename"
    set -x
    cp "$filepath" "$dest_filepath"
    sed -i -E '/\s\#\s*(cursor-only|pi-only)\s*$/d' "$dest_filepath"
    set +x
  done
fi
