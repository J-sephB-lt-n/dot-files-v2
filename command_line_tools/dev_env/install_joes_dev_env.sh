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
install_if_not_exists droast bash -c 'curl -fsL ewry.net/droast/install.sh | sh'
