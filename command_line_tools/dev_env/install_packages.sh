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

sudo apt-get update

sudo apt-get install -y bat build-essential cloc commitizen curl git jq ripgrep taskwarrior tmux tree unzip

install_if_not_exists droast bash -c 'curl -fsL https://ewry.net/droast/install.sh | sh'

install_if_not_exists dust bash -c "curl -sSfL https://raw.githubusercontent.com/bootandy/dust/refs/heads/master/install.sh | sh"

install_if_not_exists fnm bash -c 'curl -fsSL https://fnm.vercel.app/install | bash'

install_if_not_exists fzf bash -s <<'EOF'
rm -rf ~/.fzf
git clone --depth 1 https://github.com/junegunn/fzf.git ~/.fzf
~/.fzf/install --all
EOF

install_if_not_exists nvim bash -s <<'EOF'
curl -LO https://github.com/neovim/neovim/releases/latest/download/nvim-linux-x86_64.tar.gz
sudo rm -rf /opt/nvim-linux-x86_64
sudo tar -C /opt -xzf nvim-linux-x86_64.tar.gz
echo 'export PATH="$PATH:/opt/nvim-linux-x86_64/bin"' >> ~/.bashrc
EOF

install_if_not_exists pnpm bash -c 'curl -fsSL https://get.pnpm.io/install.sh | sh -'

install_if_not_exists rustc bash -c "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y"

install_if_not_exists uv bash -c 'curl -LsSf https://astral.sh/uv/install.sh | sh'

install_if_not_exists zoxide bash -s <<'EOF'
set -euo pipefail
curl -sSfL https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | sh
command -v zoxide 1>/dev/null 2>/dev/null
echo 'eval "$(zoxide init bash)"' >>~/.bashrc
EOF

echo '
# add these lines to ~/.bashrc to make neovim the default editor:
export EDITOR=nvim
export VISUAL=nvim
'
