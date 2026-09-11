#!/bin/bash

set -euo pipefail

sudo -v

install_if_not_exists() {
  if command -v "$1" 1>/dev/null 2>/dev/null; then
    echo "$1 is already installed (skipping)" >&2
    return 0
  fi

  echo "Installing $1" >&2
  shift
  "$@"
}

# droast #
install_if_not_exists droast bash -c 'curl -fsL https://ewry.net/droast/install.sh | sh'

# zoxide #
install_if_not_exists zoxide bash -s <<EOF
set -euo pipefail
curl -sSfL https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | sh
command -v zoxide 1>/dev/null 2>/dev/null
echo 'eval "$(zoxide init bash)"' >>~/.bashrc
EOF
