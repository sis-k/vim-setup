# vim-setup
Utility scripts to set up vim environment

## Neovim

```bash
python3 bootstrap_nvim.py                # report missing dependencies and set up Neovim
python3 bootstrap_nvim.py --install-deps # also install missing dependencies
```

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

CMake projects use `CMakePresets.json` if they have one, otherwise a kit from `nvim/cmake-kits.json` or the project's own `cmake-kits.json`, which sets the compilers and an optional `toolchainFile`. Cross-compilers need to be on `PATH`, which is also how `clangd` learns to trust them. Start Neovim from a shell that has them.

| Keys | Action |
|---|---|
| `<leader>mp` / `<leader>mP` | Select a configure / build preset |
| `<leader>mk` | Select a kit |
| `<leader>mt` / `<leader>mT` | Select a build type / build target |
| `<leader>mg` / `<leader>mG` | Configure / configure with options, such as `-DFOO=1` |
| `<leader>mb` | Build |
| `<leader>mc` / `<leader>mx` | Clean / stop |

To debug on a target, run `gdbserver` there, press `<leader>dc` and choose `gdbserver: connect to target`. It asks for the local program with symbols, the address and the `gdb` to use, such as `gdb-multiarch`, and remembers them for the session.
