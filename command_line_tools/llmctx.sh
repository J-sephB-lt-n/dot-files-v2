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
    llmctx insert PATH
    llmctx show [PATH ...]
    llmctx select
    llmctx rm [PATH ...]
EOF
}

check_dependencies() {
  for dep in tree fzf; do
    if ! command -v "${dep}" 1>/dev/null 2>/dev/null; then
      echo "missing required dependency: ${dep}"
      exit 1
    fi
  done
}

create_base_dir_if_not_exists() {
  if [[ ! -d "${LLMCTX_BASE_DIR}" ]]; then
    echo "Base directory ${LLMCTX_BASE_DIR} does not exist - creating it..."
    mkdir -p "${LLMCTX_BASE_DIR}"
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

show_items() {
  local missing_files=()
  local filepath abs_path name
  for filepath in "$@"; do
    abs_path="${LLMCTX_BASE_DIR}/${filepath}.llmctx"
    if [[ ! -f "${abs_path}" ]]; then
      missing_files+=("${abs_path}")
    fi
  done
  if (("${#missing_files[@]}" > 0)); then
    echo 'The following files could not be found:' >&2
    printf "  - %s\n" "${missing_files[@]}" >&2
    exit 1
  fi
  for filepath in "$@"; do
    abs_path="${LLMCTX_BASE_DIR}/${filepath}.llmctx"
    name="$(basename "${filepath}")"
    name="${name%.*}"
    echo "<${name}>"
    cat "${abs_path}"
    echo "</${name}>"
    echo ""
  done
}

select_items() {
  mapfile -t selected < <(
    find "${LLMCTX_BASE_DIR}" -type f -name "*.llmctx" -printf "%P\n" | fzf -m | sed 's/\.llmctx$//'
  )
  show_items "${selected[@]}"
}

remove_items() {
  for filepath in "$@"; do
    local abs_path="${LLMCTX_BASE_DIR}/${filepath}.llmctx"
    if [[ -f "${abs_path}" ]]; then
      rm "${abs_path}"
    else
      echo "FILE NOT FOUND: ${abs_path}"
    fi
  done
  find "${LLMCTX_BASE_DIR}" -mindepth 1 -type d -empty -delete
}

main() {
  check_dependencies
  create_base_dir_if_not_exists
  case "${1:-}" in
  help | --help | '')
    help
    ;;
  version | --version)
    echo "${LLMCTX_VERSION}"
    ;;
  ls)
    tree --noreport "${LLMCTX_BASE_DIR}" | sed 's/\.llmctx$//'
    ;;
  insert)
    shift
    insert_new_item "$@"
    ;;
  show)
    shift
    show_items "$@"
    ;;
  select)
    select_items
    ;;
  rm)
    shift
    remove_items "$@"
    ;;
  *)
    echo "Unknown command: ${1:-}"
    exit 1
    ;;
  esac
}

main "$@"
