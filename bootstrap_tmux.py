#!/usr/bin/env python3
"""Bootstrap tmux with tpm and configuration from this repository.

Steps performed:
  1. Check tmux is installed; optionally auto-install with --install-deps.
  2. Clone or update tpm (Tmux Plugin Manager) to ~/.tmux/plugins/tpm.
  3. Symlink <repo>/tmux/.tmux.conf to ~/.tmux.conf (backs up any existing file).
  4. Install all configured tpm plugins headlessly.

Usage:
  python3 bootstrap_tmux.py
  python3 bootstrap_tmux.py --install-deps
  python3 bootstrap_tmux.py --tmux-conf /tmp/test-tmux.conf
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit("Error: Python 3.10 or later is required.")

TPM_DIR = Path.home() / ".tmux" / "plugins" / "tpm"
TMUX_CONF_SRC = Path(__file__).resolve().parent / "tmux" / ".tmux.conf"
TMUX_CONF_DEST = Path.home() / ".tmux.conf"


def detect_package_manager() -> str | None:
    """Return the first supported package manager found on PATH, or None."""
    for pm in ("apt", "dnf", "pacman", "brew"):
        if shutil.which(pm):
            return pm
    return None


def parse_args() -> argparse.Namespace:
    """Parse and return command-line arguments."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--tmux-conf",
        type=Path,
        default=TMUX_CONF_DEST,
        metavar="PATH",
        help=f"Override the target tmux.conf path (default: {TMUX_CONF_DEST}).",
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Attempt to auto-install tmux if it is missing.",
    )
    return parser.parse_args()


def run(cmd: list, **kwargs) -> None:
    """Print and execute a shell command, raising on non-zero exit."""
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    subprocess.run(cmd, check=True, **kwargs)


def check_requirements() -> None:
    """Exit early if mandatory bootstrap tools (git) are missing."""
    missing = [dep for dep in ("git",) if not shutil.which(dep)]
    if missing:
        sys.exit(f"Error: missing required tools: {', '.join(missing)}")


def install_tmux(install: bool) -> None:
    """Ensure tmux is installed, optionally installing it via the package manager."""
    if existing := shutil.which("tmux"):
        result = subprocess.run(["tmux", "-V"], capture_output=True, text=True)
        print(f"tmux already installed at {existing}: {result.stdout.strip()}")
        return

    if not install:
        sys.exit(
            "Error: tmux not found. Install it manually or re-run with --install-deps."
        )

    print("Installing tmux...")
    pm = detect_package_manager()
    if not pm:
        sys.exit("Error: no supported package manager found (apt/dnf/pacman/brew). Install tmux manually.")

    packages = {"apt": "tmux", "dnf": "tmux", "pacman": "tmux", "brew": "tmux"}
    sudo = ["sudo"] if pm != "brew" else []
    install_flag = ["-y"] if pm in ("apt", "dnf") else (["--noconfirm"] if pm == "pacman" else [])
    run(sudo + [pm, "install"] + install_flag + [packages[pm]])


def install_tpm() -> None:
    """Clone or update tpm to TPM_DIR."""
    print("Setting up tpm...")
    TPM_DIR.parent.mkdir(parents=True, exist_ok=True)

    if TPM_DIR.exists():
        print(f"  tpm already cloned at {TPM_DIR}, pulling latest...")
        run(["git", "-C", str(TPM_DIR), "pull", "--quiet", "--ff-only"])
    else:
        run([
            "git", "clone", "--depth=1", "--quiet",
            "https://github.com/tmux-plugins/tpm", str(TPM_DIR),
        ])
        print(f"  Cloned tpm to {TPM_DIR}")


def symlink_conf(conf_dest: Path) -> None:
    """Symlink conf_dest to the repo's tmux/.tmux.conf.

    Backs up an existing regular file and replaces a symlink pointing elsewhere.
    """
    print("Setting up tmux config...")

    if conf_dest.is_symlink():
        target = Path(os.readlink(conf_dest))
        if not target.is_absolute():
            target = conf_dest.parent / target
        if target == TMUX_CONF_SRC:
            print(f"  Already symlinked: {conf_dest} -> {TMUX_CONF_SRC}")
            return
        conf_dest.unlink()
        print(f"  Removed existing symlink -> {target}")
    elif conf_dest.exists():
        backup = conf_dest.with_name(conf_dest.name + ".bak")
        shutil.move(str(conf_dest), str(backup))
        print(f"  Backed up existing config to {backup}")

    conf_dest.symlink_to(TMUX_CONF_SRC)
    print(f"  Symlinked: {conf_dest} -> {TMUX_CONF_SRC}")


def install_plugins() -> None:
    """Install tpm plugins headlessly using tpm's install script."""
    print("Installing tmux plugins...")
    install_script = TPM_DIR / "scripts" / "install_plugins.sh"

    if not install_script.exists():
        print(f"  Warning: tpm install script not found at {install_script}. Run prefix+I inside tmux.")
        return

    try:
        env = {**os.environ, "TMUX_PLUGIN_MANAGER_PATH": str(TPM_DIR.parent) + "/"}
        subprocess.run([str(install_script)], check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"  Warning: plugin install exited with code {e.returncode}. Run prefix+I inside tmux to retry.")


def main() -> None:
    """Entry point: parse arguments, validate inputs, and run all bootstrap steps."""
    args = parse_args()
    conf_dest = args.tmux_conf.expanduser().absolute()

    if not TMUX_CONF_SRC.is_file():
        sys.exit(f"Error: tmux config source not found at {TMUX_CONF_SRC}. Run from the repo root.")

    if conf_dest == TMUX_CONF_SRC:
        sys.exit("Error: --tmux-conf cannot point to the repo's source file.")

    print("=== tmux Bootstrap ===\n")
    if conf_dest != TMUX_CONF_DEST.expanduser().absolute():
        print(f"  Using custom tmux.conf path: {conf_dest}\n")

    check_requirements()
    install_tmux(install=args.install_deps)
    install_tpm()
    symlink_conf(conf_dest)
    install_plugins()

    print("\nDone! Start a new tmux session to apply the config.")
    print("  If plugins are missing, press prefix+I inside tmux to install them.")


if __name__ == "__main__":
    main()
