# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a personal editor configuration repository containing:
- `nvim/` — Neovim config based on [LazyVim](https://lazyvim.github.io/) starter template
- `vim/.vimrc` — Legacy Vim config (YouCompleteMe, fzf, NERDTree)

## Neovim Architecture

The nvim config follows the LazyVim structure:

- `init.lua` — Entry point; bootstraps lazy.nvim and loads `config.lazy`
- `lua/config/lazy.lua` — Plugin manager setup; imports LazyVim defaults + local `plugins/`
- `lua/config/options.lua` — Vim options loaded before plugins (4-space indent, snacks picker, autoformat off, diagnostics disabled by default)
- `lua/config/keymaps.lua` — Custom keymaps loaded on `VeryLazy` event
- `lua/config/autocmds.lua` — Custom autocmds; sets up `dap-python` using `vim.fn.stdpath("data") .. "/dap-python-env/bin/python3"`
- `lua/plugins/` — Custom plugin specs; each file returns a lazy.nvim spec table
  - `example.lua` — Template/reference file (skipped via early `return {}`)
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

`bootstrap_nvim.py` sets up a new machine:
1. Checks and optionally installs system dependencies (`--install-deps`)
2. Downloads and installs the latest Neovim binary to `~/.local/bin`
3. Symlinks `nvim/` → `~/.config/nvim` (backs up any existing config)
4. Creates a Python venv at `~/.local/share/nvim/dap-python-env` with `debugpy`
5. Pre-installs all plugins headlessly via `Lazy! sync`

```bash
python3 bootstrap_nvim.py                        # check deps, install everything
python3 bootstrap_nvim.py --install-deps         # also auto-install missing deps
python3 bootstrap_nvim.py --config-dir /tmp/test # use alternate config dir
```

System deps are declared in the `DEPS` list at the top of the script — update it when adding plugins that require new binaries. Clipboard dep is selected automatically based on `$WAYLAND_DISPLAY` (xclip vs wl-clipboard).

## Key Custom Bindings (nvim)

- `<leader><arrows>` — Window navigation
- `<S-PageUp/Down>` — Buffer prev/next
- `W` / `Y` — Select/yank current word
- `<leader>cp` / `<leader>cs` — Copilot panel/status
- `<leader>cf` / `<leader>cF` — Copy full/relative path to clipboard
