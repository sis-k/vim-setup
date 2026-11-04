-- Explicit Mason ensure_installed for tools not auto-managed by LazyVim extras.
-- LazyVim's lang/dap extras (python, clangd, markdown, etc.) handle their own
-- LSPs and DAP adapters automatically via mason-lspconfig / mason-nvim-dap.
-- The Python debug adapter is the exception: it runs through uvx (see python.lua).
-- List only additional formatters / linters here.
return {
    {
        "mason-org/mason.nvim",
        opts = {
            ensure_installed = {
                "stylua",
                "shfmt",
                "shellcheck",
            },
        },
    },
}
