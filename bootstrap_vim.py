#!/usr/bin/env python3
"""Bootstrap Vim with plugins and configuration from this repository.

Steps performed:
  1. Install Vim via the system package manager if not already present.
  2. Symlink <repo>/vim/.vimrc to ~/.vimrc (backs up any existing file).
  3. Clone fzf to ~/.fzf, build the binary, and generate ~/.fzf.bash.
  4. Symlink ~/.vim/pack/plugins/start/fzf -> ~/.fzf (single clone for both).
  5. Install fzf.vim and NERDTree as Vim 8 native packages.
  6. Generate helptags for all installed packages.

Note: YouCompleteMe is referenced in .vimrc but requires manual installation.
See: https://github.com/ycm-core/YouCompleteMe#installation

Usage:
  python3 bootstrap_vim.py
  python3 bootstrap_vim.py --vimrc /tmp/test-vimrc
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit("Error: Python 3.10 or later is required.")

PACK_DIR = Path.home() / ".vim" / "pack" / "plugins" / "start"
FZF_DIR = Path.home() / ".fzf"
VIMRC_SRC = Path(__file__).resolve().parent / "vim" / ".vimrc"
VIMRC_DEST = Path.home() / ".vimrc"

# Vim 8 native packages installed via git clone.
# fzf is handled separately by install_fzf() — do not add it here.
# Add entries when plugins require new packages.
PACKAGES = [
    ("fzf.vim",  "https://github.com/junegunn/fzf.vim.git"),
    ("nerdtree", "https://github.com/preservim/nerdtree.git"),
]


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
        "--vimrc",
        type=Path,
        default=VIMRC_DEST,
        metavar="PATH",
        help=f"Override the target vimrc path (default: {VIMRC_DEST}).",
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


def install_vim() -> None:
    """Install Vim via the system package manager if it is not already present."""
    if existing := shutil.which("vim"):
        result = subprocess.run(["vim", "--version"], capture_output=True, text=True)
        print(f"Vim already installed at {existing}: {result.stdout.splitlines()[0]}")
        return

    print("Installing Vim...")
    pm = detect_package_manager()
    if not pm:
        sys.exit("Error: no supported package manager found (apt/dnf/pacman/brew). Install vim manually.")

    packages = {"apt": "vim", "dnf": "vim-enhanced", "pacman": "vim", "brew": "vim"}
    sudo = ["sudo"] if pm != "brew" else []
    install_flag = ["-y"] if pm in ("apt", "dnf") else (["--noconfirm"] if pm == "pacman" else [])
    run(sudo + [pm, "install"] + install_flag + [packages[pm]])


def symlink_vimrc(vimrc_dest: Path) -> None:
    """Symlink vimrc_dest to the repo's vim/.vimrc.

    If vimrc_dest exists as a regular file it is backed up with a .bak suffix.
    An existing symlink pointing elsewhere is replaced.
    Uses os.readlink() to inspect the target without following the chain,
    preventing symlink loops on re-runs.
    """
    print("Setting up vimrc...")

    if vimrc_dest.is_symlink():
        target = Path(os.readlink(vimrc_dest))
        if not target.is_absolute():
            target = vimrc_dest.parent / target
        if target == VIMRC_SRC:
            print(f"  Already symlinked: {vimrc_dest} -> {VIMRC_SRC}")
            return
        vimrc_dest.unlink()
        print(f"  Removed existing symlink -> {target}")
    elif vimrc_dest.exists():
        backup = vimrc_dest.with_name(vimrc_dest.name + ".bak")
        shutil.move(str(vimrc_dest), str(backup))
        print(f"  Backed up existing vimrc to {backup}")

    vimrc_dest.symlink_to(VIMRC_SRC)
    print(f"  Symlinked: {vimrc_dest} -> {VIMRC_SRC}")


def install_fzf() -> None:
    """Clone fzf to ~/.fzf, build its binary, and wire it into Vim's pack directory.

    Runs fzf's own install script with --all --no-update-rc to build the binary
    and generate ~/.fzf.bash / ~/.fzf.zsh without modifying shell rc files.

    The Vim pack entry is a symlink to the same ~/.fzf clone rather than a
    separate checkout, keeping fzf in sync across shell and Vim usage.
    """
    print("Installing fzf...")
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    pack_link = PACK_DIR / "fzf"

    if FZF_DIR.exists():
        print(f"  fzf already cloned at {FZF_DIR}, pulling latest...")
        run(["git", "-C", str(FZF_DIR), "pull", "--quiet", "--ff-only"])
    else:
        run(["git", "clone", "--depth=1", "--quiet", "https://github.com/junegunn/fzf.git", str(FZF_DIR)])

    run([str(FZF_DIR / "install"), "--all", "--no-update-rc"])

    # Symlink into vim pack dir so vim loads the fzf plugin from the same clone
    if pack_link.is_symlink() and Path(os.readlink(pack_link)).expanduser().absolute() == FZF_DIR:
        print(f"  Vim pack symlink already set: {pack_link} -> {FZF_DIR}")
    else:
        if pack_link.is_symlink():
            pack_link.unlink()
        elif pack_link.is_dir():
            shutil.rmtree(pack_link)
        pack_link.symlink_to(FZF_DIR)
        print(f"  Symlinked vim pack: {pack_link} -> {FZF_DIR}")

    print(f"  fzf binary: {FZF_DIR / 'bin' / 'fzf'}")
    print(f"  Shell integration: source ~/.fzf.bash  (add to ~/.bashrc to persist)")


def install_packages() -> None:
    """Clone or update Vim 8 packages listed in PACKAGES, then regenerate helptags."""
    print("Installing Vim packages...")
    PACK_DIR.mkdir(parents=True, exist_ok=True)

    for name, url in PACKAGES:
        dest = PACK_DIR / name
        if dest.exists():
            print(f"  {name}: already installed, pulling latest...")
            run(["git", "-C", str(dest), "pull", "--quiet", "--ff-only"])
        else:
            print(f"  {name}: cloning...")
            run(["git", "clone", "--depth=1", "--quiet", url, str(dest)])

    run(["vim", "-u", "NONE", "-c", "packloadall | helptags ALL | qa"])
    print("  Helptags updated.")


def main() -> None:
    """Entry point: parse arguments, validate inputs, and run all bootstrap steps."""
    args = parse_args()
    vimrc_dest = args.vimrc.expanduser().absolute()

    if not VIMRC_SRC.is_file():
        sys.exit(f"Error: vimrc source not found at {VIMRC_SRC}. Run from the repo root.")

    if vimrc_dest == VIMRC_SRC:
        sys.exit("Error: --vimrc cannot point to the repo's source file.")

    print("=== Vim Bootstrap ===\n")
    if vimrc_dest != VIMRC_DEST.expanduser().absolute():
        print(f"  Using custom vimrc path: {vimrc_dest}\n")

    check_requirements()
    install_vim()
    symlink_vimrc(vimrc_dest)
    install_fzf()
    install_packages()

    print("\nNote: YouCompleteMe requires manual installation.")
    print("  See: https://github.com/ycm-core/YouCompleteMe#installation")
    print("\nDone! Launch vim to get started.")


if __name__ == "__main__":
    main()
