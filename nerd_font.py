"""Check for and install a Nerd Font, shared by bootstrap_kitty.py and bootstrap_nvim.py.

Fonts are downloaded from the latest Nerd Fonts release on GitHub and unpacked
into the per-user font folder, so no root access is needed.
"""

from __future__ import annotations  # imported before the callers check for Python 3.10

import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

# The font the repo's kitty.conf uses, and the default for Neovim's icons.
DEFAULT_FAMILY = "UbuntuSansMono Nerd Font"

# Font family -> Nerd Fonts release archive that contains it.
ARCHIVES = {
    "ubuntusansmono nerd font": "UbuntuSans",
    "ubuntumono nerd font": "UbuntuMono",
}

RELEASE_URL = "https://github.com/ryanoasis/nerd-fonts/releases/latest/download/{archive}.tar.xz"
FONT_SUFFIXES = (".ttf", ".otf")


def archive_for(family: str) -> str | None:
    """Return the release archive for a family, ignoring the Mono/Propo variant suffix."""
    name = family.casefold()
    for suffix in (" mono", " propo"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return ARCHIVES.get(name)


def font_dir(archive: str) -> Path:
    """Per-user font folder for one archive."""
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Fonts" / archive
    data_home = os.environ.get("XDG_DATA_HOME", "")
    root = Path(data_home) if data_home and Path(data_home).is_absolute() else Path.home() / ".local" / "share"
    return root / "fonts" / archive


def is_installed(family: str) -> bool | None:
    """True or False if it can tell, None if it cannot.

    Uses fc-list, not fc-match, which silently picks a fallback. Without
    fc-list (usual on macOS), looks for the files this module would install.
    """
    if shutil.which("fc-list"):
        result = subprocess.run(["fc-list", "--format=%{family}\n"], capture_output=True, text=True)
        if result.returncode == 0:
            families = {name.strip().casefold() for line in result.stdout.splitlines() for name in line.split(",")}
            return family.casefold() in families
    archive = archive_for(family)
    if archive and font_dir(archive).is_dir() and any(font_dir(archive).iterdir()):
        return True
    return None


def install(family: str) -> bool:
    """Download and unpack the archive containing family. Returns True on success."""
    archive = archive_for(family)
    if not archive:
        print(f"  Warning: don't know which Nerd Fonts archive has '{family}'. Install it manually.")
        return False
    url = RELEASE_URL.format(archive=archive)
    dest = font_dir(archive)
    print(f"  Downloading {url}")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            tarball = Path(tmp) / f"{archive}.tar.xz"
            urllib.request.urlretrieve(url, tarball)
            dest.mkdir(parents=True, exist_ok=True)
            count = 0
            with tarfile.open(tarball) as tar:
                for member in tar.getmembers():
                    # Copy font files only, by base name, so no path in the archive can escape dest.
                    if not member.isfile() or not member.name.lower().endswith(FONT_SUFFIXES):
                        continue
                    source = tar.extractfile(member)
                    if source:
                        (dest / Path(member.name).name).write_bytes(source.read())
                        count += 1
    except (OSError, tarfile.TarError) as error:
        print(f"  Warning: could not install {archive} Nerd Font: {error}")
        return False
    print(f"  Installed {count} font files to {dest}")
    if shutil.which("fc-cache"):
        subprocess.run(["fc-cache", "-f", str(dest)], check=False)
    return True


def ensure(family: str, install_missing: bool) -> None:
    """Report whether family is installed, installing it when asked."""
    state = is_installed(family)
    if state:
        print(f"Font installed: {family}")
        return
    if install_missing:
        if install(family) and is_installed(family) is not False:
            print(f"Font installed: {family}")
            return
    elif state is False:
        print(f"Warning: font '{family}' is not installed; the terminal will use a fallback.")
    else:
        print(f"Warning: could not check whether '{family}' is installed (fc-list unavailable).")
    if not install_missing:
        print("  Re-run with --install-deps to download it, or get it from https://www.nerdfonts.com/font-downloads")
