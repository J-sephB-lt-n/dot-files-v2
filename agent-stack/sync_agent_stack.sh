#!/bin/bash

set -eo pipefail

if [ -n "${OPENCODE_GLOBAL_CONFIG_DIR}" ]; then
  # --- AGENTS --- #
  find ./agents -name '*.md' -type f | while IFS= read -r filepath; do
    dest_filename=$(basename "$filepath")
    dest_filepath="$OPENCODE_GLOBAL_CONFIG_DIR/agents/$dest_filename"
    set -x
    cp "$filepath" "$dest_filepath"
    sed -i -E '/\s\#\s*(cursor-only|pi-only)\s*$/d' "$dest_filepath"
    set +x
  done

  # --- COMMANDS --- #
  find ./commands -name '*.md' -type f | while IFS= read -r filepath; do
    dest_filename=$(basename "$filepath")
    dest_filepath="$OPENCODE_GLOBAL_CONFIG_DIR/commands/$dest_filename"
    set -x
    cp "$filepath" "$dest_filepath"
    set +x
  done

  # --- SKILLS --- #
  find ./skills -name '*.md' -type f | while IFS= read -r filepath; do
    skill_dir=$(dirname "$filepath")
    skill_name=$(basename "$skill_dir")
    set -x
    cp -r "$skill_dir/." "$OPENCODE_GLOBAL_CONFIG_DIR/skills/$skill_name/"
    set +x
  done
fi

for CONFIG_DIR in "$CURSOR_GLOBAL_CONFIG_DIR" "$CURSOR_WSL_GLOBAL_CONFIG_DIR"; do
  if [ -n "${CONFIG_DIR}" ]; then
    # --- AGENTS --- #
    find ./agents -name '*.md' -type f | while IFS= read -r filepath; do
      dest_filename=$(basename "$filepath")
      dest_filepath="$CONFIG_DIR/agents/$dest_filename"
      set -x
      cp "$filepath" "$dest_filepath"
      sed -i -E '/\s\#\s*(opencode-only|pi-only)\s*$/d' "$dest_filepath"
      set +x
    done

    # --- COMMANDS --- #
    find ./commands -name '*.md' -type f | while IFS= read -r filepath; do
      dest_filename=$(basename "$filepath")
      dest_filepath="$CONFIG_DIR/commands/$dest_filename"
      set -x
      cp "$filepath" "$dest_filepath"
      set +x
    done

    # --- SKILLS --- #
    find ./skills -name '*.md' -type f | while IFS= read -r filepath; do
      skill_dir=$(dirname "$filepath")
      skill_name=$(basename "$skill_dir")
      set -x
      cp -r "$skill_dir/." "$CONFIG_DIR/skills/$skill_name/"
      set +x
    done
  fi
done
