# flatpak-tool

一个基于终端的 Flatpak 管理工具，把常用的 flatpak 操作整合进一个交互式菜单，免去记命令的麻烦。

## 功能

- **list** — 显示已安装的应用
- **search** — 搜索并安装应用
- **uninstall** — 卸载应用
- **update** — 选择并更新应用
- **update all** — 更新全部应用
- **cleanup** — 清理未使用的运行时
- **info** — 显示应用详情
- **remotes** — 显示已配置的远程仓库
- **remirror** — 更换镜像源
- **export** — 导出应用列表到文件
- **import** — 从文件安装应用
- **repair** — 修复安装
- **more** — 运行 / 权限 / 历史 / 屏蔽 / 固定

## 环境要求

- Linux 系统（Flatpak 本身主要面向 Linux）
- Python >= 3.11.9
- uv（推荐）或 pip
- Flatpak 已安装且在 PATH 中可用

## 安装

一键安装（推荐）：

    git clone https://github.com/alittleshark-dev/flatpak-tool.git
    cd flatpak-tool
    ./install.sh

安装完成后，直接运行：

    flatpak-tool

手动安装：

    git clone https://github.com/alittleshark-dev/flatpak-tool.git
    cd flatpak-tool
    uv sync

## 使用方法

直接运行：

    flatpak-tool

会看到交互式菜单，用 ↑ / ↓ 移动光标，Enter 选择，q 退出。

## 项目结构

    flatpak-tool/
    ├── src/
    │   └── flatpak_tool/
    │       └── __init__.py     # 入口（main）
    ├── install.sh              # 一键安装脚本
    ├── pyproject.toml          # 项目配置
    ├── uv.lock                 # 锁定的依赖版本
    ├── .python-version         # Python 版本声明
    └── README.md

## 卸载

    uv tool uninstall flatpak-tool

## 许可证

GPL-3.0-or-later，见 LICENSE 文件。
