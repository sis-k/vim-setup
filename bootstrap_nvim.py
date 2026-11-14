#!/usr/bin/env python3
"""Bootstrap Neovim with LazyVim configuration from this repository.

Steps performed:
  1. Check system dependencies; optionally auto-install with --install-deps.
  2. Download and install the latest Neovim binary to ~/.local/bin.
  3. Symlink <repo>/nvim/ to ~/.config/nvim (backs up any existing config).
  4. Pre-install all plugins headlessly via lazy.nvim, pinned to lazy-lock.json.

Usage:
  python3 bootstrap_nvim.py
  python3 bootstrap_nvim.py --install-deps
  python3 bootstrap_nvim.py --config-dir /tmp/nvim-test
"""

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

if sys.version_info < (3, 10):
    sys.exit("Error: Python 3.10 or later is required.")

NVIM_RELEASES_URL = "https://github.com/neovim/neovim/releases/latest/download"
LOCAL_BIN = Path.home() / ".local" / "bin"
UV_INSTALL_SCRIPT = "curl -LsSf https://astral.sh/uv/install.sh | sh"

REPO_DIR = Path(__file__).resolve().parent
NVIM_CONFIG_SRC = REPO_DIR / "nvim"


@dataclass
class Dep:
    """A system dependency required by the Neovim configuration.

    binary      -- the executable name to check via shutil.which()
    description -- human-readable description shown in reports
    required    -- if True, flagged as required; otherwise optional
    apt/dnf/pacman/brew -- package name for each supported package manager
    aliases     -- alternative binary names that also satisfy this dep
                   (e.g. 'fdfind' for 'fd' on apt systems)
    install_script -- shell command used with --install-deps when the package
                   manager has no package for this dep
    """

    binary: str
    description: str
    required: bool
    apt: str = ""
    dnf: str = ""
    pacman: str = ""
    brew: str = ""
    aliases: tuple = ()
    install_script: str = ""


def is_satisfied(dep: Dep) -> bool:
    """Return True if the dep's binary (or any alias) is found on PATH."""
    return any(shutil.which(b) for b in (dep.binary,) + dep.aliases)


IS_MACOS = platform.system() == "Darwin"
IS_WAYLAND = bool(os.environ.get("WAYLAND_DISPLAY"))

# fmt: off
# macOS has native clipboard support (pbcopy/pbpaste) -- no xclip/wl-copy needed.
CLIPBOARD_DEP = None if IS_MACOS else (
    Dep("wl-copy",  "clipboard support (Wayland)",     required=True,  apt="wl-clipboard", dnf="wl-clipboard", pacman="wl-clipboard", brew="wl-clipboard") if IS_WAYLAND else
    Dep("xclip",    "clipboard support (X11)",         required=True,  apt="xclip",        dnf="xclip",        pacman="xclip",        brew="xclip")
)

DEPS = [d for d in [
    CLIPBOARD_DEP,
    Dep("rg",       "live grep (ripgrep)",             required=True,  apt="ripgrep",    dnf="ripgrep",    pacman="ripgrep",    brew="ripgrep"),
    Dep("fd",       "file finding",                    required=True,  apt="fd-find",    dnf="fd-find",    pacman="fd",         brew="fd",    aliases=("fdfind",)),
    Dep("node",     "LSPs (Mason)",                   required=True,  apt="nodejs",     dnf="nodejs",     pacman="nodejs",     brew="node"),
    Dep("lazygit",  "git UI (gitui extra)",            required=True,  apt="lazygit",    dnf="lazygit",    pacman="lazygit",    brew="lazygit"),
    Dep("make",     "treesitter parser compilation",   required=True,  apt="make",       dnf="make",       pacman="make",       brew="make"),
    Dep("gcc",      "treesitter parser compilation",   required=True,  apt="gcc",        dnf="gcc",        pacman="gcc",        brew="gcc"),
    Dep("fzf",      "fuzzy finder (multiple plugins)", required=True,  apt="fzf",        dnf="fzf",        pacman="fzf",        brew="fzf"),
    Dep("curl",     "Mason / treesitter downloads",    required=True,  apt="curl",       dnf="curl",       pacman="curl",       brew="curl"),
    Dep("tar",      "Mason / treesitter archives",     required=True,  apt="tar",        dnf="tar",        pacman="tar",        brew="gnu-tar"),
    Dep("unzip",    "Mason package extraction",        required=True,  apt="unzip",      dnf="unzip",      pacman="unzip",      brew="unzip"),
    Dep("uvx",      "Python debugger, notebooks (uv)", required=True,  apt="",           dnf="uv",         pacman="uv",         brew="uv",    install_script=UV_INSTALL_SCRIPT),
    Dep("gitui",    "gitui binary (gitui extra)",      required=False, apt="",           dnf="",           pacman="gitui",      brew="gitui"),
    Dep("cmake",    "CMake projects",                  required=False, apt="cmake",      dnf="cmake",      pacman="cmake",      brew="cmake"),
    Dep("gdb",      "gdbserver debugging (gdb 14+)",   required=False, apt="gdb",        dnf="gdb",        pacman="gdb",        brew="gdb"),
] if d is not None]
# fmt: on


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


def run(cmd: list, **kwargs) -> None:
    """Print and execute a shell command, raising on non-zero exit."""
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    subprocess.run(cmd, check=True, **kwargs)


def check_requirements() -> None:
    """Exit early if mandatory bootstrap tools (git) are missing."""
    missing = [dep for dep in ("git",) if not shutil.which(dep)]
    if missing:
        sys.exit(f"Error: missing required tools: {', '.join(missing)}")


def nvim_tarball_name() -> str:
    """Return the correct Neovim release tarball name for the current platform."""
    system = platform.system()
    machine = platform.machine()
    if system == "Linux":
        arch = "x86_64" if machine in ("x86_64", "amd64") else "arm64"
        return f"nvim-linux-{arch}.tar.gz"
    elif system == "Darwin":
        arch = "arm64" if machine == "arm64" else "x86_64"
        return f"nvim-macos-{arch}.tar.gz"
    else:
        sys.exit(f"Error: unsupported OS '{system}'. Install Neovim manually.")


def ensure_in_path(directory: Path) -> None:
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
    """Install the latest Neovim binary to LOCAL_BIN and return its path.

    If nvim is already on PATH, skips the download and returns the existing path.
    """
    if existing := shutil.which("nvim"):
        result = subprocess.run(["nvim", "--version"], capture_output=True, text=True)
        print(f"Neovim already installed at {existing}: {result.stdout.splitlines()[0]}")
        return Path(existing)

    print("Installing Neovim...")
    LOCAL_BIN.mkdir(parents=True, exist_ok=True)

    tarball = nvim_tarball_name()
    url = f"{NVIM_RELEASES_URL}/{tarball}"
    print(f"  Downloading {url}")

    try:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            archive = tmp_path / tarball

            with urllib.request.urlopen(url) as resp, open(archive, "wb") as f:
                shutil.copyfileobj(resp, f)

            with tarfile.open(archive) as tar:
                tar.extractall(tmp_path)

            extracted = next(tmp_path.glob("nvim-*/bin/nvim"), None)
            if not extracted:
                sys.exit("Error: could not find nvim binary in downloaded archive.")

            dest = LOCAL_BIN / "nvim"
            shutil.copy2(extracted, dest)
            dest.chmod(0o755)
            print(f"  Installed to {dest}")
    except urllib.error.URLError as e:
        sys.exit(f"Error: failed to download Neovim: {e}")

    ensure_in_path(LOCAL_BIN)
    return LOCAL_BIN / "nvim"


def symlink_config(config_dir: Path) -> None:
    """Symlink config_dir to the repo's nvim/ directory.

    If config_dir already exists as a directory, it is backed up with a .bak suffix
    before the symlink is created. An existing symlink pointing elsewhere is replaced.
    """
    print("Setting up Neovim config...")

    if config_dir.is_symlink():
        target = Path(os.readlink(config_dir))
        if not target.is_absolute():
            target = config_dir.parent / target
        if target == NVIM_CONFIG_SRC:
            print(f"  Already symlinked: {config_dir} -> {NVIM_CONFIG_SRC}")
            return
        config_dir.unlink()
        print(f"  Removed existing symlink -> {target}")
    elif config_dir.exists():
        backup = config_dir.with_name(config_dir.name + ".bak")
        shutil.move(str(config_dir), str(backup))
        print(f"  Backed up existing config to {backup}")
    else:
        config_dir.parent.mkdir(parents=True, exist_ok=True)

    config_dir.symlink_to(NVIM_CONFIG_SRC)
    print(f"  Symlinked: {config_dir} -> {NVIM_CONFIG_SRC}")


def fix_fd_symlink() -> None:
    """On apt systems, fd-find installs as fdfind. Create a ~/.local/bin/fd symlink if needed."""
    if not shutil.which("fd") and (fdfind := shutil.which("fdfind")):
        LOCAL_BIN.mkdir(parents=True, exist_ok=True)
        symlink = LOCAL_BIN / "fd"
        if not symlink.exists():
            symlink.symlink_to(fdfind)
            print(f"  Created symlink: {symlink} -> {fdfind}")


def install_hint(dep: Dep, pm: str | None) -> str:
    """Return the command to suggest for installing a missing dep."""
    if pm and getattr(dep, pm):
        return f"{pm} install {getattr(dep, pm)}"
    return dep.install_script or "install manually"


def handle_deps(install: bool) -> None:
    """Check system dependencies and either report or install missing ones.

    If install is True, attempts to install via the detected package manager.
    Otherwise, prints a report and a hint to re-run with --install-deps.
    """
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
        for dep in missing_required + missing_optional:
            if pm and getattr(dep, pm):
                continue
            if not dep.install_script:
                if pm:
                    print(f"  Warning: no {pm} package known for: {dep.binary}. Install manually.")
                continue
            print(f"  Installing {dep.binary} with its install script")
            # Check for the binary, because `curl | sh` exits 0 even when the download fails.
            subprocess.run(["sh", "-c", dep.install_script], check=False)
            if not (shutil.which(dep.binary) or shutil.which(dep.binary, path=str(LOCAL_BIN))):
                print(f"  Warning: could not install {dep.binary}. Run manually: {dep.install_script}")
        fix_fd_symlink()
        return

    # Report only
    if missing_required:
        print("  Missing required dependencies:")
        for d in missing_required:
            print(f"    - {d.binary:12} {d.description} → {install_hint(d, pm)}")

    if missing_optional:
        print("  Missing optional dependencies:")
        for d in missing_optional:
            print(f"    - {d.binary:12} {d.description} → {install_hint(d, pm)}")

    print("\n  Re-run with --install-deps to install automatically.")


def bootstrap_plugins(nvim_bin: Path) -> None:
    """Run a headless Neovim session to pre-install all lazy.nvim plugins.

    Uses `Lazy! restore` so plugins are pinned to the commits in the repo's
    lazy-lock.json; `sync` would update them and rewrite the tracked lock file.
    Uses the full path to nvim_bin so this works even before PATH is reloaded
    in the current shell session.
    """
    print("Bootstrapping plugins (this may take a minute)...")
    try:
        subprocess.run(
            [str(nvim_bin), "--headless", "+Lazy! restore", "+qa"],
            check=True,
            timeout=180,
        )
    except subprocess.TimeoutExpired:
        print("  Warning: plugin sync timed out. Run ':Lazy restore' manually on first launch.")


def main() -> None:
    """Entry point: parse arguments, validate inputs, and run all bootstrap steps."""
    args = parse_args()
    config_dir = args.config_dir.expanduser().absolute()

    if not NVIM_CONFIG_SRC.is_dir():
        sys.exit(f"Error: nvim config source not found at {NVIM_CONFIG_SRC}. Run from the repo root.")

    if config_dir == NVIM_CONFIG_SRC:
        sys.exit("Error: --config-dir cannot be the same as the repo's nvim/ directory.")

    print("=== Neovim Bootstrap ===\n")
    if config_dir != (Path.home() / ".config" / "nvim").absolute():
        print(f"  Using custom config dir: {config_dir}\n")

    check_requirements()
    handle_deps(install=args.install_deps)
    nvim_bin = install_nvim()
    symlink_config(config_dir)
    bootstrap_plugins(nvim_bin)
    print("\nNote: LazyVim requires a Nerd Font for icons and the statusline to render correctly.")
    print("  Install one from https://www.nerdfonts.com and set it in your terminal emulator.")
    print("\nDone! Launch nvim to get started.")


if __name__ == "__main__":
    main()
