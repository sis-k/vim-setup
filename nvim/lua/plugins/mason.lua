-- Explicit Mason ensure_installed for tools not auto-managed by LazyVim extras.
-- LazyVim's lang/dap extras (python, clangd, markdown, etc.) handle their own
-- LSPs and DAP adapters automatically via mason-lspconfig / mason-nvim-dap.
-- List only additional formatters / linters here.
return {
    {
        "williamboman/mason.nvim",
        opts = {
            ensure_installed = {
                "stylua",
                "shfmt",
                "shellcheck",
            },
        },
    },
}
