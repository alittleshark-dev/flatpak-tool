#!/usr/bin/env bash
# Install flatpak-tool as a global command via uv tool.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "==> Project directory: $PROJECT_DIR"

# 1. 检查 uv
if ! command -v uv >/dev/null 2>&1; then
    echo "Error: uv not found."
    echo "Install it with:"
    echo "    curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "Or use your system package manager (e.g. pacman -S uv / apt install uv)."
    exit 1
fi

# 2. 检查关键文件
if [[ ! -f pyproject.toml ]]; then
    echo "Error: pyproject.toml not found in $PROJECT_DIR"
    exit 1
fi

if [[ ! -d src ]]; then
    echo "Error: src/ not found in $PROJECT_DIR"
    exit 1
fi

# 3. 用 uv tool 安装（可重复执行，会自动覆盖旧版本）
echo "==> Installing flatpak-tool ..."
uv tool install --force .

# 4. 确保 uv tool 的 bin 目录在 PATH 里
UV_BIN_DIR="$(uv tool dir --bin 2>/dev/null || echo "$HOME/.local/bin")"
if ! echo "$PATH" | tr ':' '\n' | grep -qx "$UV_BIN_DIR"; then
    echo
    echo "Note: $UV_BIN_DIR is not in your PATH."
    echo "Run this to add it automatically:"
    echo
    echo "    uv tool update-shell"
    echo
    echo "Or add this line to your ~/.zshrc manually:"
    echo
    echo "    export PATH=\"$UV_BIN_DIR:\$PATH\""
    echo
fi

# 5. 验证
if command -v flatpak-tool >/dev/null 2>&1; then
    echo
    echo "==> Installed successfully!"
    echo "    Run it with:  flatpak-tool"
else
    echo
    echo "==> Installed, but 'flatpak-tool' is not yet in PATH."
    echo "    Either open a new terminal, or run:"
    echo "      export PATH=\"$UV_BIN_DIR:\$PATH\""
    echo "    Then run:  flatpak-tool"
fi
