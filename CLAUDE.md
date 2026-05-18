# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a personal editor configuration repository containing:
- `nvim/` — Neovim config based on [LazyVim](https://lazyvim.github.io/) starter template
- `vim/.vimrc` — Legacy Vim config (YouCompleteMe, fzf, NERDTree)
- `tmux/.tmux.conf` — tmux config (vi keys, mouse, tpm)
- `bootstrap_nvim.py` — Automated Neovim setup script
- `bootstrap_vim.py` — Automated Vim setup script
- `bootstrap_tmux.py` — Automated tmux setup script

## Neovim Architecture

The nvim config follows the LazyVim structure:

- `init.lua` — Entry point; bootstraps lazy.nvim and loads `config.lazy`
- `lua/config/lazy.lua` — Plugin manager setup; imports LazyVim defaults + local `plugins/`
- `lua/config/options.lua` — Vim options loaded before plugins (4-space indent, snacks picker, autoformat off, diagnostics disabled by default)
- `lua/config/keymaps.lua` — Custom keymaps loaded on `VeryLazy` event
- `lua/config/autocmds.lua` — Custom autocmds; sets up `dap-python` using `vim.fn.stdpath("data") .. "/dap-python-env/bin/python3"`
- `lua/plugins/` — Custom plugin specs; each file returns a lazy.nvim spec table
  - `example.lua` — Template/reference file (skipped via early `return {}`)
  - `mason.lua` — Explicit Mason `ensure_installed` for extra formatters/linters
  - `vstasks.lua` — VS Code tasks integration via `vs-tasks.nvim` with snacks picker
  - `dashboard.lua` — Customizes snacks.nvim dashboard header

## LazyVim Extras Enabled

Configured in `lazyvim.json`: copilot, copilot-chat, luasnip, dap.core, dap.nlua, overseer, clangd, git, markdown, python, gitui, project.

## Formatting

Lua files use [stylua](https://github.com/JohnnyMorganz/StyLua) with settings from `stylua.toml`:
- 4-space indentation, 120 column width

To format: `stylua nvim/`

## Adding Plugins

Create a new file in `nvim/lua/plugins/` returning a lazy.nvim spec table. All files in that directory are auto-loaded. Use `example.lua` as a reference (it is ignored at runtime).

## Bootstrap

Both scripts require Python 3.10+ and `git`. Run from the repo root.

**Neovim** — `bootstrap_nvim.py`:
1. Checks and optionally installs system dependencies (`--install-deps`)
2. Downloads and installs the latest Neovim binary to `~/.local/bin`
3. Symlinks `nvim/` → `~/.config/nvim` (backs up any existing config)
4. Creates a Python venv at `~/.local/share/nvim/dap-python-env` with `debugpy`
5. Pre-installs all plugins headlessly via `Lazy! sync`

```bash
python3 bootstrap_nvim.py                         # check deps, install everything
python3 bootstrap_nvim.py --install-deps          # also auto-install missing deps
python3 bootstrap_nvim.py --config-dir /tmp/test  # use alternate config dir
```

System deps are declared in the `DEPS` list at the top of the script — update it when adding plugins that require new binaries. Clipboard dep is selected automatically based on `$WAYLAND_DISPLAY` (xclip vs wl-clipboard).

**Vim** — `bootstrap_vim.py`:
1. Installs Vim via the system package manager if missing
2. Symlinks `vim/.vimrc` → `~/.vimrc` (backs up any existing file)
3. Clones fzf to `~/.fzf`, builds the binary, generates `~/.fzf.bash`
4. Symlinks `~/.vim/pack/plugins/start/fzf` → `~/.fzf` (single clone for both)
5. Installs `fzf.vim` and `NERDTree` as Vim 8 native packages

```bash
python3 bootstrap_vim.py                          # install everything
python3 bootstrap_vim.py --vimrc /tmp/test-vimrc  # use alternate vimrc path
```

Add new Vim plugins to the `PACKAGES` list at the top of the script. YouCompleteMe requires [manual installation](https://github.com/ycm-core/YouCompleteMe#installation).

**tmux** — `bootstrap_tmux.py`:
1. Checks and optionally installs tmux (`--install-deps`)
2. Clones or updates tpm to `~/.tmux/plugins/tpm`
3. Symlinks `tmux/.tmux.conf` → `~/.tmux.conf` (backs up any existing file)
4. Installs all tpm plugins headlessly

```bash
python3 bootstrap_tmux.py                               # install everything
python3 bootstrap_tmux.py --install-deps                # also auto-install tmux
python3 bootstrap_tmux.py --tmux-conf /tmp/test.conf    # use alternate conf path
```

## Mason Packages (nvim)

LazyVim extras auto-manage their own LSPs and DAP adapters via Mason (e.g., `pyright` from `lang.python`, `clangd` from `lang.clangd`). Additional tools (formatters, linters) are pinned explicitly in `lua/plugins/mason.lua` via `ensure_installed`. Add entries there when a new formatter or linter is needed.

## Key Custom Bindings (nvim)

- `<leader><arrows>` — Window navigation
- `<S-PageUp/Down>` — Buffer prev/next
- `W` / `Y` — Select/yank current word
- `<leader>cp` / `<leader>cs` — Copilot panel/status
- `<leader>cf` / `<leader>cF` — Copy full/relative path to clipboard
