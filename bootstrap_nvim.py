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
from pathlib import Path

NVIM_RELEASES_URL = "https://github.com/neovim/neovim/releases/latest/download"
LOCAL_BIN = Path.home() / ".local" / "bin"
DATA_DIR = Path.home() / ".local" / "share" / "nvim"
DAP_VENV = DATA_DIR / "dap-python-env"

REPO_DIR = Path(__file__).resolve().parent
NVIM_CONFIG_SRC = REPO_DIR / "nvim"


def parse_args():
    parser = argparse.ArgumentParser(description="Bootstrap Neovim with LazyVim configuration.")
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path.home() / ".config" / "nvim",
        metavar="DIR",
        help="Override the target config directory (default: ~/.config/nvim).",
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


def install_nvim():
    if existing := shutil.which("nvim"):
        result = subprocess.run(["nvim", "--version"], capture_output=True, text=True)
        print(f"Neovim already installed at {existing}: {result.stdout.splitlines()[0]}")
        return

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

    if str(LOCAL_BIN) not in os.environ.get("PATH", "").split(":"):
        print(f"  Warning: {LOCAL_BIN} is not in your PATH. Add it to your shell profile.")


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


def bootstrap_plugins():
    print("Bootstrapping plugins (this may take a minute)...")
    try:
        subprocess.run(
            ["nvim", "--headless", "+Lazy! sync", "+qa"],
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
    install_nvim()
    symlink_config(config_dir)
    setup_dap_python()
    bootstrap_plugins()
    print("\nDone! Launch nvim to get started.")


if __name__ == "__main__":
    main()
