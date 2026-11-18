-- Inline image rendering via the kitty graphics protocol (snacks.nvim image module).
-- Requires: kitty (or Ghostty/WezTerm) and ImageMagick (`brew install imagemagick`).
-- Optional: ghostscript (PDF), mermaid-cli (mermaid), tectonic (LaTeX math).
-- Inline markdown images need conceallevel >= 2, set below for markdown only when the terminal supports images
-- (otherwise it would just hide link syntax). Run `:checkhealth snacks` to see if the terminal is detected.
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
                    local ok, supported = pcall(function()
                        return Snacks.image.supports_terminal()
                    end)
                    if ok and supported then
                        vim.opt_local.conceallevel = 2
                    end
                end,
            })
        end,
    },
}
