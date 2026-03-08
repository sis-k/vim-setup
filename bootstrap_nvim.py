#!/usr/bin/env python3
"""Bootstrap Neovim with LazyVim configuration from this repository."""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

NVIM_RELEASES_URL = "https://github.com/neovim/neovim/releases/latest/download"
LOCAL_BIN = Path.home() / ".local" / "bin"
DATA_DIR = Path.home() / ".local" / "share" / "nvim"
DAP_VENV = DATA_DIR / "dap-python-env"

REPO_DIR = Path(__file__).resolve().parent
NVIM_CONFIG_SRC = REPO_DIR / "nvim"


@dataclass
class Dep:
    # Binary to check with shutil.which()
    binary: str
    description: str
    required: bool
    # Package name per package manager; omit a key to mark as unsupported
    apt: str = ""
    dnf: str = ""
    pacman: str = ""
    brew: str = ""
    # Alternative binary names that also satisfy this dep (e.g. fdfind for fd on apt)
    aliases: tuple = ()


def is_satisfied(dep: Dep) -> bool:
    return any(shutil.which(b) for b in (dep.binary,) + dep.aliases)


IS_WAYLAND = bool(os.environ.get("WAYLAND_DISPLAY"))

# fmt: off
DEPS = [
    Dep("wl-copy",  "clipboard support (Wayland)",     required=True,  apt="wl-clipboard", dnf="wl-clipboard", pacman="wl-clipboard", brew="wl-clipboard") if IS_WAYLAND else
    Dep("xclip",    "clipboard support (X11)",         required=True,  apt="xclip",        dnf="xclip",        pacman="xclip",        brew="xclip"),
    Dep("rg",       "live grep (ripgrep)",             required=True,  apt="ripgrep",    dnf="ripgrep",    pacman="ripgrep",    brew="ripgrep"),
    Dep("fd",       "file finding",                    required=True,  apt="fd-find",    dnf="fd-find",    pacman="fd",         brew="fd",    aliases=("fdfind",)),
    Dep("node",     "Copilot and LSPs",                required=True,  apt="nodejs",     dnf="nodejs",     pacman="nodejs",     brew="node"),
    Dep("lazygit",  "git UI (gitui extra)",            required=True,  apt="lazygit",    dnf="lazygit",    pacman="lazygit",    brew="lazygit"),
    Dep("make",     "treesitter parser compilation",   required=True,  apt="make",       dnf="make",       pacman="make",       brew="make"),
    Dep("gcc",      "treesitter parser compilation",   required=True,  apt="gcc",        dnf="gcc",        pacman="gcc",        brew="gcc"),
    Dep("fzf",      "fuzzy finder (multiple plugins)", required=True,  apt="fzf",        dnf="fzf",        pacman="fzf",        brew="fzf"),
    Dep("gitui",    "gitui binary (gitui extra)",      required=False, apt="",           dnf="",           pacman="gitui",      brew="gitui"),
]
# fmt: on


def detect_package_manager() -> str | None:
    for pm in ("apt", "dnf", "pacman", "brew"):
        if shutil.which(pm):
            return pm
    return None


def parse_args():
    parser = argparse.ArgumentParser(description="Bootstrap Neovim with LazyVim configuration.")
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path.home() / ".config" / "nvim",
        metavar="DIR",
        help="Override the target config directory (default: ~/.config/nvim).",
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Attempt to auto-install missing system dependencies.",
    )
    return parser.parse_args()


def run(cmd, **kwargs):
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    subprocess.run(cmd, check=True, **kwargs)


def check_requirements():
    missing = [dep for dep in ("git",) if not shutil.which(dep)]
    if missing:
        print(f"Error: missing required tools: {', '.join(missing)}")
        sys.exit(1)


def nvim_tarball_name():
    system = platform.system()
    machine = platform.machine()
    if system == "Linux":
        arch = "x86_64" if machine in ("x86_64", "amd64") else "arm64"
        return f"nvim-linux-{arch}.tar.gz"
    elif system == "Darwin":
        arch = "arm64" if machine == "arm64" else "x86_64"
        return f"nvim-macos-{arch}.tar.gz"
    else:
        print(f"Unsupported OS: {system}")
        sys.exit(1)


def ensure_in_path(directory: Path):
    """Append directory to PATH in the user's shell profile if not already present."""
    if str(directory) in os.environ.get("PATH", "").split(":"):
        return
    shell = Path(os.environ.get("SHELL", "")).name
    profile = {
        "bash": Path.home() / ".bashrc",
        "zsh": Path.home() / ".zshrc",
    }.get(shell, Path.home() / ".profile")
    line = f'\nexport PATH="{directory}:$PATH"\n'
    existing = profile.read_text() if profile.exists() else ""
    if str(directory) in existing:
        return
    with open(profile, "a") as f:
        f.write(line)
    print(f"  Added {directory} to {profile} — run 'source {profile}' or open a new shell.")


def install_nvim() -> Path:
    if existing := shutil.which("nvim"):
        result = subprocess.run(["nvim", "--version"], capture_output=True, text=True)
        print(f"Neovim already installed at {existing}: {result.stdout.splitlines()[0]}")
        return Path(existing)

    print("Installing Neovim...")
    LOCAL_BIN.mkdir(parents=True, exist_ok=True)

    tarball = nvim_tarball_name()
    url = f"{NVIM_RELEASES_URL}/{tarball}"
    print(f"  Downloading {url}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        archive = tmp_path / tarball

        with urllib.request.urlopen(url) as resp, open(archive, "wb") as f:
            shutil.copyfileobj(resp, f)

        with tarfile.open(archive) as tar:
            tar.extractall(tmp_path)

        extracted = next(tmp_path.glob("nvim-*/bin/nvim"), None)
        if not extracted:
            print("Error: could not find nvim binary in archive.")
            sys.exit(1)

        dest = LOCAL_BIN / "nvim"
        shutil.copy2(extracted, dest)
        dest.chmod(0o755)
        print(f"  Installed to {dest}")

    ensure_in_path(LOCAL_BIN)
    return LOCAL_BIN / "nvim"


def symlink_config(config_dir: Path):
    print("Setting up Neovim config...")

    if config_dir.is_symlink():
        existing = config_dir.resolve()
        if existing == NVIM_CONFIG_SRC:
            print(f"  Already symlinked: {config_dir} -> {NVIM_CONFIG_SRC}")
            return
        config_dir.unlink()
        print(f"  Removed existing symlink -> {existing}")
    elif config_dir.exists():
        backup = config_dir.with_name(config_dir.name + ".bak")
        shutil.move(str(config_dir), str(backup))
        print(f"  Backed up existing config to {backup}")
    else:
        config_dir.parent.mkdir(parents=True, exist_ok=True)

    config_dir.symlink_to(NVIM_CONFIG_SRC)
    print(f"  Symlinked: {config_dir} -> {NVIM_CONFIG_SRC}")


def setup_dap_python():
    print("Setting up dap-python virtual environment...")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not (DAP_VENV / "bin" / "python3").exists():
        run([sys.executable, "-m", "venv", str(DAP_VENV)])
    else:
        print(f"  Venv already exists at {DAP_VENV}")

    pip = DAP_VENV / "bin" / "pip"
    run([str(pip), "install", "--quiet", "debugpy"])
    print(f"  debugpy installed in {DAP_VENV}")


def fix_fd_symlink():
    """On apt systems, fd-find installs as fdfind. Create a fd symlink if needed."""
    if not shutil.which("fd") and (fdfind := shutil.which("fdfind")):
        LOCAL_BIN.mkdir(parents=True, exist_ok=True)
        symlink = LOCAL_BIN / "fd"
        if not symlink.exists():
            symlink.symlink_to(fdfind)
            print(f"  Created symlink: {symlink} -> {fdfind}")


def handle_deps(install: bool):
    print("Checking system dependencies...")
    pm = detect_package_manager()

    missing_required = [d for d in DEPS if d.required and not is_satisfied(d)]
    missing_optional = [d for d in DEPS if not d.required and not is_satisfied(d)]

    if not missing_required and not missing_optional:
        print("  All dependencies satisfied.")
        fix_fd_symlink()
        return

    if install:
        if not pm:
            print("  Warning: no supported package manager found (apt/dnf/pacman/brew). Install manually.")
        else:
            to_install = [getattr(d, pm) for d in missing_required + missing_optional if getattr(d, pm)]
            if to_install:
                sudo = ["sudo"] if pm != "brew" else []
                install_flag = "-y" if pm in ("apt", "dnf") else ("--noconfirm" if pm == "pacman" else "")
                cmd = sudo + [pm, "install"] + ([install_flag] if install_flag else []) + to_install
                print(f"  Installing via {pm}: {', '.join(to_install)}")
                run(cmd)
            unsupported = [d.binary for d in missing_required + missing_optional if not getattr(d, pm)]
            if unsupported:
                print(f"  Warning: no {pm} package known for: {', '.join(unsupported)}. Install manually.")
        fix_fd_symlink()
        return

    # Report only
    if missing_required:
        print("  Missing required dependencies:")
        for d in missing_required:
            pkg_hint = getattr(d, pm) if pm and getattr(d, pm) else d.binary
            install_cmd = f"{pm} install {pkg_hint}" if pm else d.binary
            print(f"    - {d.binary:12} {d.description} → {install_cmd}")

    if missing_optional:
        print("  Missing optional dependencies:")
        for d in missing_optional:
            pkg_hint = getattr(d, pm) if pm and getattr(d, pm) else d.binary
            install_cmd = f"{pm} install {pkg_hint}" if pm else d.binary
            print(f"    - {d.binary:12} {d.description} → {install_cmd}")

    print("\n  Re-run with --install-deps to install automatically.")


def bootstrap_plugins(nvim_bin: Path):
    print("Bootstrapping plugins (this may take a minute)...")
    try:
        subprocess.run(
            [str(nvim_bin), "--headless", "+Lazy! sync", "+qa"],
            check=True,
            timeout=180,
        )
    except subprocess.TimeoutExpired:
        print("  Warning: plugin sync timed out. Run ':Lazy sync' manually on first launch.")


def main():
    args = parse_args()
    config_dir = args.config_dir.resolve()

    print("=== Neovim Bootstrap ===\n")
    if config_dir != Path.home() / ".config" / "nvim":
        print(f"  Using custom config dir: {config_dir}\n")

    check_requirements()
    handle_deps(install=args.install_deps)
    nvim_bin = install_nvim()
    symlink_config(config_dir)
    setup_dap_python()
    bootstrap_plugins(nvim_bin)
    print("\nNote: LazyVim requires a Nerd Font for icons and the statusline to render correctly.")
    print("  Install one from https://www.nerdfonts.com and set it in your terminal emulator.")
    print("\nDone! Launch nvim to get started.")


if __name__ == "__main__":
    main()
