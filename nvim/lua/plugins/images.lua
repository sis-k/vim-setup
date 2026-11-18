-- Inline image rendering via the kitty graphics protocol (snacks.nvim image module).
-- Requires: kitty (or Ghostty/WezTerm) and ImageMagick (`brew install imagemagick`).
-- Optional: ghostscript (PDF), mermaid-cli (mermaid), tectonic (LaTeX math).
-- Inline markdown images need conceallevel >= 2 (set below for markdown).
-- Under tmux: `set -g allow-passthrough on`.
return {
    {
        "folke/snacks.nvim",
        opts = {
            image = { enabled = true },
        },
    },
    {
        "LazyVim/LazyVim",
        init = function()
            vim.api.nvim_create_autocmd("FileType", {
                pattern = { "markdown" },
                callback = function()
                    vim.opt_local.conceallevel = 2
                end,
            })
        end,
    },
}
