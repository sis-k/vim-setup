#!/usr/bin/env python3
"""Bootstrap Kitty with configuration from this repository.

Checks Kitty is installed, optionally installs it with --install-deps, and
symlinks kitty/kitty.conf into the user's configuration directory. Existing
files and unrelated symlinks are backed up without replacing earlier backups.
Checks the configured Nerd Font is installed; --install-deps also downloads it.

Usage:
  python3 bootstrap_kitty.py
  python3 bootstrap_kitty.py --install-deps
  python3 bootstrap_kitty.py --kitty-conf /tmp/test-kitty.conf
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import nerd_font

if sys.version_info < (3, 10):
    sys.exit("Error: Python 3.10 or later is required.")

KITTY_CONF_SRC = Path(__file__).resolve().parent / "kitty" / "kitty.conf"


def default_config_path() -> Path:
    """Follow Kitty's lookup: $KITTY_CONFIG_DIRECTORY, then an absolute $XDG_CONFIG_HOME, then ~/.config."""
    if kitty_dir := os.environ.get("KITTY_CONFIG_DIRECTORY"):
        return Path(kitty_dir).expanduser() / "kitty.conf"
    config_home = os.environ.get("XDG_CONFIG_HOME", "")
    root = Path(config_home) if config_home and Path(config_home).is_absolute() else Path.home() / ".config"
    return root / "kitty" / "kitty.conf"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--kitty-conf", type=Path, default=default_config_path(), metavar="PATH",
        help=f"Override the target kitty.conf path (default: {default_config_path()}).",
    )
    parser.add_argument(
        "--install-deps", action="store_true",
        help="Install Kitty and the configured Nerd Font if they are missing.",
    )
    return parser.parse_args()


# Where the macOS app (dmg, cask or Kitty's installer) and Kitty's Linux installer put it.
# These copies are often not on PATH.
KITTY_APP_BINARIES = [
    Path("/Applications/kitty.app/Contents/MacOS/kitty"),
    Path.home() / "Applications" / "kitty.app" / "Contents" / "MacOS" / "kitty",
    Path.home() / ".local" / "kitty.app" / "bin" / "kitty",
]


def find_kitty() -> tuple[str, bool] | None:
    """Return Kitty's path and whether it is on PATH, or None if not installed."""
    if existing := shutil.which("kitty"):
        return existing, True
    for binary in KITTY_APP_BINARIES:
        if binary.is_file() and os.access(binary, os.X_OK):
            return str(binary), False
    return None


def install_kitty(install: bool) -> None:
    if found := find_kitty():
        path, on_path = found
        print(f"Kitty already installed at {path}")
        if not on_path:
            print("  Note: the kitty command is not on PATH (not needed to use the app). To add it:")
            print(f"  ln -s {path} ~/.local/bin/kitty")
        return
    if not install:
        sys.exit("Error: Kitty not found. Install it manually or re-run with --install-deps.")

    commands = {
        "apt": ["apt", "install", "-y", "kitty"],
        "dnf": ["dnf", "install", "-y", "kitty"],
        "pacman": ["pacman", "-S", "--needed", "--noconfirm", "kitty"],
    }
    # Homebrew ships Kitty only as a macOS cask; there is no Linux formula.
    if sys.platform == "darwin":
        commands = {"brew": ["brew", "install", "--cask", "kitty"]}
    for manager, command in commands.items():
        if shutil.which(manager):
            if manager != "brew" and os.geteuid() != 0:
                command = ["sudo"] + command
            print(f"  $ {' '.join(command)}")
            subprocess.run(command, check=True)
            return
    sys.exit("Error: no supported package manager found (apt/dnf/pacman/brew). Install Kitty manually.")


def configured_font() -> str:
    """The font_family set in the repo's kitty.conf, or Kitty's default."""
    family = "monospace"
    for line in KITTY_CONF_SRC.read_text().splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2 and parts[0] == "font_family":
            family = parts[1].strip()
    return family


def check_font(install: bool) -> None:
    family = configured_font()
    if family != "monospace":
        nerd_font.ensure(family, install)


def validate_destination(destination: Path) -> None:
    if not KITTY_CONF_SRC.is_file():
        sys.exit(f"Error: Kitty config source not found: {KITTY_CONF_SRC}")
    # Resolve parent aliases without following the config symlink itself.
    if destination.parent.resolve() / destination.name == KITTY_CONF_SRC:
        sys.exit("Error: --kitty-conf cannot point to the repo's source file.")
    if not destination.is_symlink() and destination.exists():
        if destination.samefile(KITTY_CONF_SRC):
            sys.exit("Error: --kitty-conf cannot point to the repo's source file.")
        if not destination.is_file():
            sys.exit(f"Error: config destination is not a regular file: {destination}")


def symlink_conf(destination: Path) -> None:
    validate_destination(destination)
    if destination.is_symlink() and destination.resolve() == KITTY_CONF_SRC:
        print(f"Already symlinked: {destination} -> {KITTY_CONF_SRC}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(destination):
        backup = destination.with_name(destination.name + ".bak")
        suffix = 1
        while os.path.lexists(backup):
            backup = destination.with_name(f"{destination.name}.bak.{suffix}")
            suffix += 1
        destination.rename(backup)
        print(f"Backed up existing config to {backup}")
    destination.symlink_to(KITTY_CONF_SRC)
    print(f"Symlinked: {destination} -> {KITTY_CONF_SRC}")


def main() -> None:
    args = parse_args()
    destination = args.kitty_conf.expanduser().absolute()
    validate_destination(destination)
    install_kitty(args.install_deps)
    check_font(args.install_deps)
    symlink_conf(destination)
    print("Done! Restart Kitty or press Ctrl+Shift+F5 to reload the config.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, subprocess.CalledProcessError) as error:
        sys.exit(f"Error: {error}")
