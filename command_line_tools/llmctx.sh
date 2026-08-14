#!/usr/bin/env bash
# To make globally available:
#   1. chmod +x llmctx.sh
#   2. ln -s /home/josephbbolton/command_line_tools/llmctx.sh ~/.local/bin/llmctx
#   3. now you can run `llmctx --help` from any folder

LLMCTX_VERSION='
  llmctx
  bash cli tool for managing llm agent context
  (interface inspired by \`pass\`)

  v0.1.0
  joseph bolton
'

LLMCTX_BASE_DIR=~/.llmctx

help() {
  cat <<EOF
  $LLMCTX_VERSION

  USAGE:
    llmctx --help
    llmctx --version
    llmctx ls
    llmctx insert item-name
    llmctx show [--full] item-name
    llmctx rm item-name
EOF
}

create_base_dir_if_not_exists() {
  if [[ ! -d "${LLMCTX_BASE_DIR}" ]]; then
    echo "Base directory ${LLMCTX_BASE_DIR} does not exist - creating it..."
    mkdir "${LLMCTX_BASE_DIR}"
    echo "Created directory ${LLMCTX_BASE_DIR}"
  fi
}

main() {
  create_base_dir_if_not_exists
  case "${1:-}" in
  help | --help | '')
    help
    ;;
  version | --version)
    echo "${LLMCTX_VERSION}"
    ;;
  *)
    echo "Unknown command: ${1:-}"
    exit 1
    ;;
  esac
}

main "$@"
