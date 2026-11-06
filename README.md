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
