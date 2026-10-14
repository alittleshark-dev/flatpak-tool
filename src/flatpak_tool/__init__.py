#!/usr/bin/env python3
"""Flatpak TUI Manager — powered by simple-term-menu"""

import subprocess
import sys
from pathlib import Path
from simple_term_menu import TerminalMenu

MIRRORS = {
    "ustc":     ("USTC (China)", "https://mirrors.ustc.edu.cn/flathub"),
    "sjtug":    ("SJTUG (China)", "https://mirrors.sjtug.sjtu.edu.cn/flathub"),
    "cernet":   ("CERNET (auto)", "https://mirrors.cernet.edu.cn/flathub"),
    "official": ("Official", "https://dl.flathub.org/repo"),
}

UPDATE_TIMEOUT = 180


def run(cmd: list, capture: bool = False, timeout: int | None = None):
    if not capture:
        print(f"\n>>> {' '.join(cmd)}\n")
    try:
        result = subprocess.run(
            cmd, check=True, capture_output=capture,
            text=True, timeout=timeout,
        )
        return result.stdout if capture else None
    except subprocess.TimeoutExpired:
        print(f"\nTimed out after {timeout}s: {' '.join(cmd)}")
        return "" if capture else None
    except subprocess.CalledProcessError as e:
        print(f"\nCommand failed, exit code: {e.returncode}")
        return "" if capture else None
    except FileNotFoundError:
        print("\nError: flatpak not found. Is it installed?")
        sys.exit(1)


def pause():
    input("\nPress Enter to continue...")


def installed_app_ids() -> set[str]:
    """返回已安装应用的 application id 集合。"""
    out = run(["flatpak", "list", "--app", "--columns=application"], capture=True)
    if not out:
        return set()
    return {line.strip() for line in out.strip().splitlines() if line.strip()}


def get_current_mirror() -> str:
    out = run(["flatpak", "remotes", "--columns=name,url"], capture=True)
    if not out:
        return "unknown"
    for line in out.strip().splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0] == "flathub":
            return parts[1]
    return "unknown"


def pick_app(title: str) -> str | None:
    out = run(["flatpak", "list", "--columns=application,version"], capture=True)
    if not out or not out.strip():
        print("\nNo apps installed.")
        return None

    apps, labels = [], []
    for line in out.strip().splitlines():
        parts = line.split("\t")
        app_id = parts[0]
        version = parts[1] if len(parts) > 1 else ""
        apps.append(app_id)
        labels.append(f"{app_id}  ({version})")

    menu = TerminalMenu(labels, title=title, cycle_cursor=True, clear_screen=True)
    idx = menu.show()
    if idx is None:
        return None
    return apps[idx]


def pick_many(title: str, items: list[str], preset: list[bool] | None = None):
    """多选菜单，返回选中项的索引列表。"""
    menu = TerminalMenu(
        items,
        title=title,
        multi_select=True,
        show_multi_select_hint=True,
        cycle_cursor=True,
        clear_screen=True,
        preselected_entries=preset,
    )
    menu.show()
    return list(menu.chosen_indices) if menu.chosen_indices else []


# ---------- 基础功能 ----------

def do_list():
    out = run(
        ["flatpak", "list",
         "--columns=name,application,version,branch,origin"],
        capture=True,
    )
    if not out or not out.strip():
        print("\nNo flatpak apps installed.")
        return

    print("\n" + "=" * 92)
    print(f"{'Name':<26}{'Application ID':<38}{'Version':<12}{'Branch':<10}{'Origin':<10}")
    print("-" * 92)
    for line in out.strip().splitlines():
        parts = line.split("\t")
        while len(parts) < 5:
            parts.append("")
        name, app_id, version, branch, origin = parts[:5]
        name_disp = name if len(name) <= 24 else name[:21] + "..."
        print(f"{name_disp:<26}{app_id:<38}{version:<12}{branch:<10}{origin:<10}")
    print("=" * 92)


def do_search():
    keyword = input("Search keyword: ").strip()
    if not keyword:
        return
    out = run(
        ["flatpak", "search", keyword,
         "--columns=name,application,version,branch,remotes"],
        capture=True,
    )
    if not out or not out.strip():
        print(f"\nNo results for '{keyword}'.")
        return

    installed = installed_app_ids()

    print("\n" + "=" * 100)
    print(f"{'':<12}{'Name':<26}{'Application ID':<38}{'Version':<12}{'Branch':<10}{'Remote':<10}")
    print("-" * 100)
    for line in out.strip().splitlines():
        parts = line.split("\t")
        while len(parts) < 5:
            parts.append("")
        name, app_id, version, branch, remote = parts[:5]
        mark = "[installed]" if app_id in installed else ""
        name_disp = name if len(name) <= 24 else name[:21] + "..."
        print(f"{mark:<12}{name_disp:<26}{app_id:<38}{version:<12}{branch:<10}{remote:<10}")
    print("=" * 100)

    ans = input("\nInstall one of these? Enter application ID (or blank to skip): ").strip()
    if ans:
        do_install(ans)


def do_install(app_id: str | None = None):
    if app_id is None:
        app_id = input("Application ID (e.g. org.mozilla.firefox): ").strip()
    if not app_id:
        return
    print(f"\nInstalling {app_id} ...")
    run(["flatpak", "install", "-y", "flathub", app_id])


def do_uninstall():
    app_id = pick_app("Select app to uninstall:")
    if not app_id:
        return
    if input(f"\nUninstall {app_id}? [y/N] ").strip().lower() == "y":
        run(["flatpak", "uninstall", "-y", app_id])


def do_uninstall_unused():
    out = run(["flatpak", "uninstall", "--unused", "--dry-run"], capture=True)
    if not out or not out.strip():
        print("\nNothing to clean up.")
        return
    print("\nThe following unused runtimes will be removed:\n")
    print(out)
    if input("Proceed? [y/N] ").strip().lower() == "y":
        run(["flatpak", "uninstall", "--unused", "-y"])


def do_update():
    """先列出可更新项，多选后更新。"""
    out = run(["flatpak", "remote-ls", "--updates",
               "--columns=application,version,branch"],
              capture=True)
    if not out or not out.strip():
        print("\nEverything is up to date.")
        return

    apps, labels = [], []
    for line in out.strip().splitlines():
        parts = line.split("\t")
        app_id = parts[0]
        version = parts[1] if len(parts) > 1 else ""
        branch = parts[2] if len(parts) > 2 else ""
        apps.append(app_id)
        labels.append(f"{app_id}  {version}  ({branch})")

    chosen = pick_many(
        "Select apps to update (space to toggle, enter to confirm):",
        labels,
        preset=[True] * len(labels),
    )
    if not chosen:
        print("Nothing selected.")
        return

    selected = [apps[i] for i in chosen]
    print(f"\nUpdating {len(selected)} app(s) (timeout {UPDATE_TIMEOUT}s)...")
    for app_id in selected:
        run(["flatpak", "update", "-y", app_id], timeout=UPDATE_TIMEOUT)


def do_update_all():
    print(f"\nRunning flatpak update -y (timeout {UPDATE_TIMEOUT}s)...")
    run(["flatpak", "update", "-y"], timeout=UPDATE_TIMEOUT)


def do_info():
    app_id = pick_app("Select app for info:")
    if app_id:
        run(["flatpak", "info", app_id])


def do_remotes():
    out = run(["flatpak", "remotes", "-d"], capture=True)
    if out:
        print("\n" + out)


def do_repair():
    if input("Run flatpak repair? Requires sudo. [y/N] ").strip().lower() == "y":
        run(["sudo", "flatpak", "repair"])


def do_remirror():
    keys = list(MIRRORS.keys())
    labels = [f"{MIRRORS[k][0]}  —  {MIRRORS[k][1]}" for k in keys]

    menu = TerminalMenu(labels, title="Select a mirror for flathub:",
                        cycle_cursor=True, clear_screen=True)
    idx = menu.show()
    if idx is None:
        return
    key = keys[idx]
    name, url = MIRRORS[key]
    print(f"\nSwitching to: {name}")
    run(["sudo", "flatpak", "remote-modify", "flathub", "--url", url])


# ---------- 导出 / 导入 ----------

DEFAULT_EXPORT = Path.home() / "flatpak-apps.txt"


def do_export():
    out = run(["flatpak", "list", "--app", "--columns=application"], capture=True)
    if not out or not out.strip():
        print("\nNo apps to export.")
        return
    apps = [l.strip() for l in out.strip().splitlines() if l.strip()]

    path_str = input(f"Export to [{DEFAULT_EXPORT}]: ").strip()
    path = Path(path_str) if path_str else DEFAULT_EXPORT
    path.write_text("\n".join(apps) + "\n", encoding="utf-8")
    print(f"\nExported {len(apps)} app(s) to {path}")


def do_import():
    path_str = input(f"Import from [{DEFAULT_EXPORT}]: ").strip()
    path = Path(path_str) if path_str else DEFAULT_EXPORT
    if not path.exists():
        print(f"\nFile not found: {path}")
        return

    apps = [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not apps:
        print("\nFile is empty.")
        return

    installed = installed_app_ids()
    to_install = [a for a in apps if a not in installed]
    already = [a for a in apps if a in installed]

    print(f"\nTotal in file: {len(apps)}")
    print(f"Already installed: {len(already)}")
    print(f"To install: {len(to_install)}")
    if already:
        print("  (already installed: " + ", ".join(already) + ")")
    if not to_install:
        print("\nNothing to install.")
        return

    print("\nTo install:")
    for a in to_install:
        print(f"  {a}")

    if input("\nProceed? [y/N] ").strip().lower() != "y":
        return

    for app_id in to_install:
        print(f"\n--- Installing {app_id} ---")
        run(["flatpak", "install", "-y", "flathub", app_id])


# ---------- More 子菜单功能 ----------

def do_run_app():
    app_id = pick_app("Select app to run:")
    if app_id:
        print(f"\nLaunching {app_id} ...")
        try:
            subprocess.Popen(["flatpak", "run", app_id])
            print("Launched (detached).")
        except FileNotFoundError:
            print("Error: flatpak not found.")


def do_permissions():
    keys = ["show", "reset", "remove", "set"]
    labels = [
        "show    — view app permissions",
        "reset   — reset app to default permissions",
        "remove  — remove a permission entry",
        "set     — set a permission entry",
    ]
    menu = TerminalMenu(labels, title="Permissions:",
                        cycle_cursor=True, clear_screen=True)
    idx = menu.show()
    if idx is None:
        return

    action = keys[idx]

    if action == "show":
        app_id = pick_app("Select app to show permissions:")
        if app_id:
            run(["flatpak", "permissions", app_id])
    elif action == "reset":
        app_id = pick_app("Select app to reset permissions:")
        if app_id and input(f"Reset permissions for {app_id}? [y/N] ").strip().lower() == "y":
            run(["flatpak", "permission-reset", app_id])
    elif action == "remove":
        app_id = pick_app("Select app:")
        if not app_id:
            return
        run(["flatpak", "permissions", app_id])
        entry = input("\nPermission entry to remove (e.g. filesystems=host): ").strip()
        if entry:
            run(["flatpak", "permission-remove", app_id, entry])
    elif action == "set":
        app_id = pick_app("Select app:")
        if not app_id:
            return
        entry = input("Permission entry to set (e.g. filesystems=home): ").strip()
        if entry:
            run(["flatpak", "permission-set", app_id, entry])


def do_history():
    out = run(["flatpak", "history", "--columns=time,change,application,version"],
              capture=True)
    if out and out.strip():
        print("\n" + out)
    else:
        print("\nNo history.")


def do_mask():
    keys = ["mask", "unmask"]
    labels = [
        "mask   — prevent updates & auto-install for an app",
        "unmask — remove a mask",
    ]
    menu = TerminalMenu(labels, title="Mask / Unmask:",
                        cycle_cursor=True, clear_screen=True)
    idx = menu.show()
    if idx is None:
        return

    action = keys[idx]
    app_id = pick_app(f"Select app to {action}:")
    if not app_id:
        return

    if action == "mask":
        if input(f"Mask {app_id}? [y/N] ").strip().lower() == "y":
            run(["flatpak", "mask", app_id])
    else:
        if input(f"Unmask {app_id}? [y/N] ").strip().lower() == "y":
            run(["flatpak", "mask", "--remove", app_id])


def do_pin():
    keys = ["pin", "unpin"]
    labels = [
        "pin   — pin a runtime to prevent auto-removal",
        "unpin — remove a pin",
    ]
    menu = TerminalMenu(labels, title="Pin / Unpin:",
                        cycle_cursor=True, clear_screen=True)
    idx = menu.show()
    if idx is None:
        return

    action = keys[idx]
    app_id = pick_app(f"Select app to {action}:")
    if not app_id:
        return

    if action == "pin":
        if input(f"Pin {app_id}? [y/N] ").strip().lower() == "y":
            run(["flatpak", "pin", app_id])
    else:
        if input(f"Unpin {app_id}? [y/N] ").strip().lower() == "y":
            run(["flatpak", "pin", "--remove", app_id])


def do_more():
    options = [
        "run         — launch an installed app",
        "permissions — view / modify app permissions",
        "history     — show operation history",
        "mask        — mask / unmask an app",
        "pin         — pin / unpin an app or runtime",
        "back",
    ]
    while True:
        menu = TerminalMenu(options, title="More",
                            cycle_cursor=True, clear_screen=True)
        idx = menu.show()

        if idx is None or idx == 5:
            return
        elif idx == 0:
            do_run_app(); pause()
        elif idx == 1:
            do_permissions(); pause()
        elif idx == 2:
            do_history(); pause()
        elif idx == 3:
            do_mask(); pause()
        elif idx == 4:
            do_pin(); pause()


# ---------- 主菜单 ----------

def main():
    while True:
        current = get_current_mirror()
        options = [
            "list        — show installed apps",
            "search      — search & install apps",
            "uninstall   — remove an app",
            "update      — pick & update apps",
            "update all  — update everything",
            "cleanup     — remove unused runtimes",
            "info        — show app details",
            "remotes     — show configured remotes",
            f"remirror    — change mirror   [now: {current}]",
            "export      — export app list to file",
            "import      — install apps from file",
            "repair      — repair installation",
            "more        — run / permissions / history / mask / pin",
            "quit",
        ]

        menu = TerminalMenu(options, title="Flatpak Manager",
                            cycle_cursor=True, clear_screen=True)
        idx = menu.show()

        if idx is None or idx == 13:
            print("Bye.")
            break
        elif idx == 0:
            do_list(); pause()
        elif idx == 1:
            do_search(); pause()
        elif idx == 2:
            do_uninstall(); pause()
        elif idx == 3:
            do_update(); pause()
        elif idx == 4:
            do_update_all(); pause()
        elif idx == 5:
            do_uninstall_unused(); pause()
        elif idx == 6:
            do_info(); pause()
        elif idx == 7:
            do_remotes(); pause()
        elif idx == 8:
            do_remirror(); pause()
        elif idx == 9:
            do_export(); pause()
        elif idx == 10:
            do_import(); pause()
        elif idx == 11:
            do_repair(); pause()
        elif idx == 12:
            do_more()


if __name__ == "__main__":
    main()
