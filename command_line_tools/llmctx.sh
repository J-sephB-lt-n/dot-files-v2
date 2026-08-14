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

insert_new_item() {
  if [[ $# -ne 1 || -z "$1" ]]; then
    echo 'Usage: llmctx insert item-name'
    exit 1
  fi
  local itempath="$1"
  echo "${itempath}"
  local itemdir=""
  local item_filename
  item_filename=$(basename "${itempath}")
  if [[ "${itempath}" == */* ]]; then
    itemdir=$(dirname "${itempath}")
  fi
  if [[ -n "${itemdir}" ]]; then
    mkdir -p "${LLMCTX_BASE_DIR}/${itemdir}"
  fi
  local item_filepath="${LLMCTX_BASE_DIR}/${itemdir}/${item_filename}.llmctx"
  if [[ -f "${item_filepath}" ]]; then
    echo "There is already a context item at path ${item_filepath}"
    exit 1
  fi
  : >"${item_filepath}"
  local text_editor="${VISUAL:-${EDITOR:-vi}}"
  "${text_editor}" "${item_filepath}"

  echo "Insert new context item ${item_filepath}"
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
  ls)
    tree --noreport "${LLMCTX_BASE_DIR}"
    ;;
  insert)
    shift
    insert_new_item "$@"
    ;;
  *)
    echo "Unknown command: ${1:-}"
    exit 1
    ;;
  esac
}

main "$@"
