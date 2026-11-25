# vim-setup
Utility scripts to set up vim environment

## Neovim

```bash
python3 bootstrap_nvim.py                # report missing dependencies and set up Neovim
python3 bootstrap_nvim.py --install-deps # also install missing dependencies
```

LazyVim needs a [Nerd Font](https://www.nerdfonts.com) for its icons and statusline. `--install-deps` downloads UbuntuSansMono Nerd Font into your user font folder (`~/.local/share/fonts`, or `~/Library/Fonts` on macOS); set it as your terminal's font. Over SSH the font belongs on the machine running the terminal, so the script skips it there.

[uv](https://docs.astral.sh/uv/) is required for the Python debugger and the notebook commands. `--install-deps` installs it with the package manager, or with uv's official installer on apt systems, which have no uv package. Without that flag, a missing `uv` is only reported, so install it yourself:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Notebooks

Opening an `.ipynb` file shows it as read-only `# %%` Python, so `:w` can't change the notebook.

| Keys | Command | Action |
|---|---|---|
| `<leader>je` | `:NbScript [path]` | Export the notebook to a `.py` next to it, or to `path`. Never overwrites a file. |
| `<leader>js` | `:NbServe` | Start JupyterLab from the project root, or reopen its page if it's running. |
| `<leader>jq` | `:NbStop` | Stop the server and its kernels. It also stops when Neovim exits. |

### C++ and CMake

CMake projects use their `CMakePresets.json`. For a project you configure by hand, add a `CMakeUserPresets.json` with your toolchain file and options, or pass them with `<leader>mG`. Cross-compilers need to be on `PATH`, which is also how `clangd` learns to trust them. Start Neovim from a shell that has them.

| Keys | Action |
|---|---|
| `<leader>mp` | Select a configure preset, and its build preset (asks if it has several, uses `None` if it has none) |
| `<leader>mP` | Select a build preset, and its configure preset. `None` builds the configure preset's folder directly. |
| `<leader>mk` | Select a kit, from the project's `cmake-kits.json`. Each kit builds in its own `out/<kit>/<build type>` folder. |
| `<leader>mt` / `<leader>mT` | Select a build type / build target. Targets are only known after configuring, so `<leader>mT` configures first if needed. A build preset that lists its own targets overrides `<leader>mT`; pick `None` with `<leader>mP` to choose freely. |
| `<leader>mg` / `<leader>mG` | Configure / configure with options, such as `-DFOO=1` |
| `<leader>mb` | Build, configuring first if the selected build folder hasn't been configured |
| `<leader>mc` / `<leader>mx` | Clean / stop |

Selecting a preset, kit or build type doesn't configure. Configure with `<leader>mg`, with your options with `<leader>mG`, or let `<leader>mb` do it. Options given with `<leader>mG` stay in CMake's cache until you clean or set them again.

To debug on a target, run `gdbserver` there, press `<leader>dc` and choose `gdbserver: connect to target`. It asks for the local program with symbols, the address and the `gdb` to use, and remembers them for the session. It uses gdb's own DAP mode, which needs gdb 14 or newer built with Python. For other architectures, install `gdb-multiarch`, which it then suggests. gdb stops where the program is waiting when it connects, so press `<leader>dc` again to run to your first breakpoint.

## Kitty (optional)

```bash
python3 bootstrap_kitty.py                              # requires Kitty already installed
python3 bootstrap_kitty.py --install-deps               # also install Kitty if missing
python3 bootstrap_kitty.py --kitty-conf /tmp/kitty.conf  # use an alternate config path
```

Requires Python 3.10+. The script symlinks `kitty/kitty.conf` to
`~/.config/kitty/kitty.conf` (or `$KITTY_CONFIG_DIRECTORY/kitty.conf`, or
`$XDG_CONFIG_HOME/kitty/kitty.conf` when set to an absolute path). Existing files and unrelated symlinks are moved to `.bak`,
`.bak.1`, etc., preserving previous backups. Re-running with the correct symlink
does nothing. Keep this repository in place while using the symlink.

`--install-deps` supports apt, dnf, pacman, and Homebrew (macOS only), and also
downloads the configured Nerd Font if it is missing. The config uses
**UbuntuSansMono Nerd Font at 12 pt** and **F11 to toggle fullscreen**. To use
another font, change `font_family` in `kitty/kitty.conf`. Font detection uses
`fc-list` when available. Restart Kitty or press **Ctrl+Shift+F5** to apply
config changes.

This bootstrap doesn't depend on the Neovim, Vim, or tmux scripts.
